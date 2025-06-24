#include <random>

#include <llvm/Analysis/ConstantFolding.h>
#include <llvm/Passes/PassBuilder.h>
#include <llvm/Passes/PassPlugin.h>

#include "obfuscate.h"

static std::random_device rd;

struct InterpreterContext final
{
	explicit InterpreterContext(const llvm::Module& m) : layout(m.getDataLayout()) {}
	InterpreterContext(const InterpreterContext&) = delete;

	const llvm::DataLayout& layout;
	std::unordered_map<const llvm::Instruction*, llvm::Constant*> locals;
};

struct GMOPass final : llvm::PassInfoMixin<GMOPass>
{
	llvm::PreservedAnalyses run(const llvm::Module& module, llvm::ModuleAnalysisManager&)
	{
		runInner(module);
		return llvm::PreservedAnalyses::all();
	}

private:
	llvm::ConstantInt* loadValue(const llvm::Value* ptr) const
	{
		if (ptr != input)
			return nullptr;
		const auto elementType = llvm::Type::getInt16Ty(ptr->getContext());
		return llvm::ConstantInt::get(elementType, apple.row() | (static_cast<uint16_t>(apple.col()) << 8));
	}

	bool LLVM_ATTRIBUTE_ALWAYS_INLINE execLoad(InterpreterContext& ctx, const llvm::LoadInst& inst,
											   const llvm::Constant* ptr) const
	{
		llvm::Constant* loaded;

		if (const auto gep = llvm::dyn_cast<llvm::GEPOperator>(ptr); gep != nullptr)
		{
			const auto cst = loadValue(gep->getPointerOperand());
			if (cst == nullptr)
				return false;

			const std::vector<llvm::Value*> indices{gep->idx_begin(), gep->idx_end()};
			const int64_t offset = ctx.layout.getIndexedOffsetInType(gep->getSourceElementType(), indices);
			loaded = ConstantFoldLoadFromConst(cst, inst.getType(), llvm::APInt(64, offset, true), ctx.layout);
		}
		else
		{
			const auto cst = loadValue(ptr);
			if (cst == nullptr)
				return false;
			loaded = ConstantFoldLoadFromConst(cst, inst.getType(), ctx.layout);
		}

		if (loaded == nullptr)
			return false;

		ctx.locals.insert_or_assign(&inst, loaded);
		return true;
	}

	bool LLVM_ATTRIBUTE_ALWAYS_INLINE execStore(const llvm::Constant* ptr, const llvm::Constant* value)
	{
		if (ptr != output)
			return false;

		const auto cstInt = llvm::dyn_cast_if_present<llvm::ConstantInt>(value);
		if (cstInt == nullptr)
			return false;

		move = static_cast<Direction>(cstInt->getZExtValue());
		return true;
	}

	static llvm::Constant* valueToConstant(const InterpreterContext& ctx, llvm::Value* const value)
	{
		if (const auto cst = llvm::dyn_cast<llvm::Constant>(value); cst != nullptr)
			return cst;

		const auto opInst = llvm::dyn_cast<llvm::Instruction>(value);
		if (opInst == nullptr)
			return nullptr;

		if (const auto it = ctx.locals.find(opInst); it != ctx.locals.end())
			return it->second;

		return nullptr;
	}

	LLVM_ATTRIBUTE_ALWAYS_INLINE bool runInstruction(InterpreterContext& ctx, const llvm::Instruction& inst)
	{
		if (!tick())
			return false;

		std::vector<llvm::Constant*> operands;
		operands.reserve(inst.getNumOperands());
		for (const auto& op : inst.operands())
		{
			const auto cst = valueToConstant(ctx, op);
			if (cst == nullptr)
				return false;
			operands.push_back(cst);
		}

		if (const auto load = llvm::dyn_cast<llvm::LoadInst>(&inst); load != nullptr)
			return execLoad(ctx, *load, operands[0]);

		if (const auto store = llvm::dyn_cast<llvm::StoreInst>(&inst); store != nullptr)
			return execStore(operands[1], operands[0]);

		if (auto folded = ConstantFoldInstOperands(const_cast<llvm::Instruction*>(&inst), operands, ctx.layout);
			folded != nullptr)
		{
			ctx.locals.insert_or_assign(&inst, folded);
			return true;
		}

		return false;
	}

#ifndef NDEBUG
	void debugDisplay(const InterpreterContext& ctx, const llvm::Instruction& inst)
	{
		llvm::outs() << "tick " << tickCount << ":\n";
		for (uint8_t i = 0; i < ROWS; ++i)
		{
			for (uint8_t j = 0; j < COLS; ++j)
			{
				if (body.front() == Position{i, j})
					llvm::outs() << '0';
				else if (std::ranges::contains(body, Position{i, j}))
					llvm::outs() << 'O';
				else if (apple == Position{i, j})
					llvm::outs() << 'A';
				else
					llvm::outs() << '.';
			}
			llvm::outs() << '\n';
		}
		llvm::outs() << "ate count: " << static_cast<int>(ateCount) << '\n';
		// llvm::outs() << "locals:\n";
		// for (const auto& [key, cst] : ctx.locals)
		// {
		// 	if (cst != nullptr)
		// 		llvm::outs() << *key << " -> " << *cst << '\n';
		// 	else
		// 		llvm::outs() << *key << " -> null\n";
		// }
		llvm::outs() << "instruction: " << inst << '\n';
		llvm::outs() << "uses:\n";
		for (const auto& use : inst.operands())
		{
			if (!llvm::isa<llvm::Instruction>(use))
				continue;

			if (const auto constant = valueToConstant(ctx, use); constant != nullptr)
				llvm::outs() << *use << " -> " << *constant << '\n';
			else
				llvm::outs() << *use << " -> null\n";
		}
		llvm::outs() << "------------------\n";
	}
#endif

	static bool fillPhi(InterpreterContext& ctx, const llvm::BasicBlock* oldBB, const llvm::BasicBlock* bb,
						llvm::BasicBlock::const_iterator& instIt)
	{
		std::unordered_map<const llvm::Instruction*, llvm::Constant*> newLocals = ctx.locals;

		for (instIt = bb->begin(); instIt != bb->end(); ++instIt)
		{
			const auto phi = llvm::dyn_cast<llvm::PHINode>(instIt);
			if (phi == nullptr)
				break;

			auto cst = valueToConstant(ctx, phi->getIncomingValueForBlock(oldBB));
			if (cst == nullptr)
				return false;

			newLocals.insert_or_assign(phi, cst);
		}

		newLocals.swap(ctx.locals);
		return true;
	}

	bool runMainFunction(InterpreterContext&& ctx, const llvm::Function* const func)
	{
		const llvm::BasicBlock* bb = &func->getEntryBlock();

		for (auto instIt = bb->begin(); instIt != bb->end();)
		{
#ifndef NDEBUG
			debugDisplay(ctx, *instIt);
#endif

			if (const auto ret = llvm::dyn_cast<llvm::ReturnInst>(&*instIt); ret != nullptr)
				return true;

			if (const auto br = llvm::dyn_cast<llvm::BranchInst>(&*instIt); br != nullptr)
			{
				if (br->isConditional())
				{
					const auto condition = valueToConstant(ctx, br->getCondition());
					if (condition == nullptr)
						return false;

					if (condition->isNullValue())
					{
						const llvm::BasicBlock* newBB = br->getSuccessor(1);
						if (!fillPhi(ctx, bb, newBB, instIt))
							return false;
						bb = newBB;
						continue;
					}
				}

				const llvm::BasicBlock* newBB = br->getSuccessor(0);
				if (!fillPhi(ctx, bb, newBB, instIt))
					return false;
				bb = newBB;
				continue;
			}

			if (const auto switch_ = llvm::dyn_cast<llvm::SwitchInst>(&*instIt); switch_ != nullptr)
			{
				const auto cond = valueToConstant(ctx, switch_->getCondition());
				if (cond == nullptr)
					return false;

				bool matched = false;
				for (const auto& caseIt : switch_->cases())
					if (caseIt.getCaseValue() == cond)
					{
						const llvm::BasicBlock* newBB = caseIt.getCaseSuccessor();
						if (!fillPhi(ctx, bb, newBB, instIt))
							return false;
						bb = newBB;
						matched = true;
						break;
					}

				if (!matched)
				{
					const llvm::BasicBlock* newBB = switch_->getDefaultDest();
					if (!fillPhi(ctx, bb, newBB, instIt))
						return false;
					bb = newBB;
				}

				continue;
			}

			if (!runInstruction(ctx, *instIt))
				return false;

			++instIt;
		}
		return false;
	}

	LLVM_ATTRIBUTE_ALWAYS_INLINE bool tick()
	{
		if (++tickCount > TICK_LIMIT)
			return false;

		// move the snake
		auto head = body.front();
		if (!head.move(move))
			return false;

		if (head != apple)
			body.pop_back();

		// check head intersect with body
		if (std::ranges::contains(body, head))
			return false;
		body.push_front(head);

		if (head == apple)
		{
			do
			{
#ifndef NDEBUG
				if (apples.empty())
				{
					std::uniform_int_distribution<uint8_t> dist(0, ROWS * COLS - 1);
					apple = Position(dist(rd));
				}
				else
				{
					apple = apples.back();
					apples.pop_back();
				}
#else
				std::uniform_int_distribution<uint8_t> dist(0, ROWS * COLS - 1);
				apple = Position(dist(rd));
#endif
			}
			while (std::ranges::contains(body, apple));

			++ateCount;
		}

		return true;
	}

	LLVM_ATTRIBUTE_ALWAYS_INLINE void runInner(const llvm::Module& module)
	{
		if (!checkInput(module) || !checkOutput(module))
			return;

		const auto main = module.getFunction(llvm::StringRef(AY_OBFUSCATE("main"), std::strlen("main")));
		if (main == nullptr)
			return;

		if (main->arg_size() != 0)
			return;

		if (!main->getReturnType()->isVoidTy())
			return;

		if (!runMainFunction(InterpreterContext(module), main))
			return;

		if (ateCount != APPLE_COUNT)
			return;

		llvm::outs() << "Congratulations! Flag: IERAE{FAKE FLAG}\n";
	}

	LLVM_ATTRIBUTE_ALWAYS_INLINE bool checkInput(const llvm::Module& module)
	{
		input = module.getGlobalVariable(llvm::StringRef(AY_OBFUSCATE("input"), std::strlen("input")));
		return input != nullptr;
	}

	LLVM_ATTRIBUTE_ALWAYS_INLINE bool checkOutput(const llvm::Module& module)
	{
		output = module.getGlobalVariable(llvm::StringRef(AY_OBFUSCATE("output"), std::strlen("output")));
		if (output == nullptr)
			return false;
		if (!output->hasInitializer())
			return false;
		const auto initializer = llvm::dyn_cast<const llvm::ConstantInt>(output->getInitializer());
		if (initializer == nullptr)
			return false;
		move = static_cast<Direction>(initializer->getZExtValue());
		return true;
	}

	llvm::GlobalVariable* input;
	llvm::GlobalVariable* output;

	enum Direction : uint8_t
	{
		UP = 0,
		DOWN = 1,
		LEFT = 2,
		RIGHT = 3
	} move;

	static constexpr uint8_t ROWS = 15;
	static constexpr uint8_t COLS = 17;
	static constexpr uint8_t APPLE_COUNT = (ROWS + COLS) * 2;
	static constexpr uint64_t TICK_LIMIT = ROWS * COLS * APPLE_COUNT * .3;
	struct Position
	{
		explicit Position(const uint8_t pos_) : pos(pos_) {}
		Position(const uint8_t row, const uint8_t col) : pos(row * COLS + col) {}
		bool operator==(const Position&) const = default;

		[[nodiscard]] uint8_t LLVM_ATTRIBUTE_ALWAYS_INLINE row() const { return pos / COLS; }
		[[nodiscard]] uint8_t LLVM_ATTRIBUTE_ALWAYS_INLINE col() const { return pos % COLS; }

		[[nodiscard]] bool LLVM_ATTRIBUTE_ALWAYS_INLINE move(const Direction dir)
		{
			switch (dir)
			{
			case UP:
				if (row() == 0)
					return false;
				pos -= COLS;
				return true;
			case DOWN:
				if (row() == ROWS - 1)
					return false;
				pos += COLS;
				return true;
			case LEFT:
				if (col() == 0)
					return false;
				--pos;
				return true;
			case RIGHT:
				if (col() == COLS - 1)
					return false;
				++pos;
				return true;
			default:
				return false;
			}
		}

	private:
		uint8_t pos;
	};

	std::list<Position> body = {
		{ROWS / 2, 3},
		{ROWS / 2, 2},
		{ROWS / 2, 1},
	};

	Position apple = {ROWS / 2, COLS - 5};

#ifndef NDEBUG
	std::vector<Position> apples = {
		// {0, COLS - 2},
	};
#endif

	uint8_t ateCount = 0;
	uint64_t tickCount = 0;
};

extern "C" LLVM_ATTRIBUTE_WEAK LLVM_ATTRIBUTE_VISIBILITY_DEFAULT llvm::PassPluginLibraryInfo llvmGetPassPluginInfo()
{
	return {LLVM_PLUGIN_API_VERSION, "GMOPass", LLVM_VERSION_STRING, [](llvm::PassBuilder& pb)
			{
				pb.registerOptimizerLastEPCallback(
					[](llvm::ModulePassManager& mpm, const llvm::OptimizationLevel l)
					{
						if (l == llvm::OptimizationLevel::O3)
							mpm.addPass(GMOPass());
					});
			}};
}
