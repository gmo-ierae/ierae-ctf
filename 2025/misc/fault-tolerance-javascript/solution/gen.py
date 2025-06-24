BUFFER = ""

def gen_double_assign(x, y, val):
  global BUFFER

  BUFFER += f"{x}={y}={val};\n"

gen_double_assign("aa00", "isNaN ", " `/**/`//*`/**/")
gen_double_assign("aa00", "isFinite ", " `/**/`//*`/**/")

gen_double_assign("xxx00", "escape ", ' `/**/console.log("hello");process.exit(0);`//*`/**/')
gen_double_assign("xxx00", "unescape ", ' `/**/console.log("hello");process.exit(0);`//*`/**/')

gen_double_assign("yyy00", "decodeURI ", ' `/**/console.log("hello");process.exit(0);`//*`/**/')
gen_double_assign("yyy00", "encodeURI ", ' `/**/console.log("hello");process.exit(0);`//*`/**/')

def gen_var_def(var):
  gen_double_assign(var, "aa", "00")

def gen_neighvar_def(var):
  declared = []

  for i in range(len(var)):
    neighbor = var[:i] + var[i+1:]
    
    if neighbor in declared:
      continue
    declared.append(neighbor)

    gen_var_def(neighbor)

gen_neighvar_def("xxx00")

gen_var_def("pppxxx00")
gen_var_def("xxx00length")

gen_double_assign("aa", "ppp", "xxx00.length")
gen_double_assign("aa", "ppp", "xxx00.length")

gen_neighvar_def("yyy00")

gen_var_def("qqqyyy00")
gen_var_def("yyy00length")

gen_double_assign("aa", "qqq", "yyy00.length")
gen_double_assign("aa", "qqq", "yyy00.length")

gen_var_def("pp")
gen_var_def("qq")

LEN = len('/**/console.log("hello");process.exit(0);')

BUFFER += f'ppp-={LEN};\n'
BUFFER += f'qqq-={LEN};\n'

gen_var_def("pp")
gen_var_def("qq")
gen_neighvar_def("eval")
gen_neighvar_def("xxx00")
gen_neighvar_def("yyy00")

gen_var_def("aaeval")
gen_var_def("valaa")
gen_var_def("ealaa")
gen_var_def("evlaa")
gen_var_def("evaaa")
gen_var_def("evalcallaa")

gen_double_assign('val', 'aa', 'eval')
gen_double_assign('eal', 'aa', 'eval')
gen_double_assign('evl', 'aa', 'eval')
gen_double_assign('eva', 'aa', 'eval')
gen_double_assign('evalcall', 'aa', 'eval')

gen_double_assign('eval.all', 'aa', 'eval.call')
gen_double_assign('eval.cll', 'aa', 'eval.call')
gen_double_assign('eval.cal', 'aa', 'eval.call')

BUFFER += 'ppp || eval.call`;aa;//${xxx00}}/*`//*`/**/;\n'
BUFFER += 'ppp || eval.call`;aa;//${xxx00}}/*`//*`/**/;\n'

BUFFER += 'qqq || eval.call`;aa;//${yyy00}}/*`//*`/**/;\n'
BUFFER += 'qqq || eval.call`;aa;//${yyy00}}/*`//*`/**/;\n'

print(BUFFER)
