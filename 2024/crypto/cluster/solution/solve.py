from Crypto.Util.number import isPrime, long_to_bytes
from tqdm import tqdm

p = 1
q = 1
r = 1

max_bit = 1024

def check(ls:list) -> bool:
    p, q, r = ls
    return (p + q) ** 2 + (q + r) ** 2 + (r + p) ** 2 == 12 * p * q * r

# Diophantine Equation Tree
class DE_tree:
    def __init__(self, p, q, r, prev_rule, depth):
        assert check([p, q, r])
        self.p = p
        self.q = q
        self.r = r
        self.prev_rule = prev_rule
        self.depth = depth
        self.is_end = any([self.p.bit_length() > max_bit, self.q.bit_length() > max_bit, self.r.bit_length() > max_bit])

    def __str__(self) -> str:
        return f'[+] {self.depth=}, {self.p=}, {self.q=}, {self.r=}'


def rule_a(node:DE_tree) -> DE_tree:
    new_p = (node.q ** 2 + node.q * node.r + node.r ** 2) // node.p
    return DE_tree(new_p, node.q, node.r, 'a', node.depth + 1)
    
def rule_b(node:DE_tree) -> DE_tree:
    new_q = (node.p ** 2 + node.p * node.r + node.r ** 2) // node.q
    return DE_tree(node.p, new_q, node.r, 'b', node.depth + 1)
    
def rule_c(node:DE_tree) -> DE_tree:
    new_r = (node.p ** 2 + node.p * node.q + node.q ** 2) // node.r
    return DE_tree(node.p, node.q, new_r, 'c', node.depth + 1)


def add_node(node:DE_tree) -> None:
    global tree_list
    if node.prev_rule == None:
        tree_list.append(rule_a(node))
    else:
        if node.prev_rule == 'a':
            tree_list.append(rule_b(node))
            tree_list.append(rule_c(node))
        if node.prev_rule == 'b':
            tree_list.append(rule_c(node))
            tree_list.append(rule_a(node))
        if node.prev_rule == 'c':
            tree_list.append(rule_a(node))
            tree_list.append(rule_b(node))

def add_node_batch(depth:int) -> bool:
    global tree_list
    update_flag = False
    for node in tree_list:
        if node.depth == depth and not node.is_end:
            add_node(node)
            update_flag = True
    return update_flag


init = DE_tree(p, q, r, None, 0)
tree_list = [init]

i = 0
while True: 
    flag = add_node_batch(i)
    if not flag:
        print(f'[+] all node is made')
        break
    i += 1
    if i % 40 == 0:
        print(f'[*] depth {i} creating...')

e = 65537
c = 803065078252547393812982498895211019353977926969143481455672761264443519482121067346644328911375984166893647468186232810673857290127114177258405196432172412966170401425497369188710097376895361641046391686887615687734454887428130745946475159776034046370464137762008371294039825175819408224450178007611894599399705434991448459196552982074660952318580952594830076838718297573226980847848142642550316589863549823042663312178673956251841439218528410295177672591802052069297783

for node in tqdm(tree_list):
    if all([isPrime(node.p), isPrime(node.q), isPrime(node.r)]):
        print(node)
        try:
            p, q, r = node.p, node.q, node.r
            n = p * q * r
            phi = (p-1) * (q-1) * (r-1)
            d = pow(e, -1, phi)
            print(f'[+] {long_to_bytes(pow(c, d, n))}')
        except:
            pass