from sage.all import *
import flag

BITS = 88
K = 8


def random(lower_bound=0, upper_bound=2 ^ BITS, bits=None):
    return ZZ.random_element(lower_bound, upper_bound)


def random_bits(bits):
    return random(2 ^ (bits - 1), 2 ^ bits)


(x1, x2, x3) = (
    1337,
    108758038897050520831860923441402897201224898270547825657705075428051130846061735614252293345445641285591980004736447964462956581141116321772403519125859758137648644808920743070411296325521866392898376475395494,
    5438451076181919949694350690364579526012926958491719881284366792649670689294870931317007945903275017524668258922051576064401873439529896167369498669912618211164397682696947429627504905294350782410183543966679528,
)
(y1, y2, y3) = (
    2356240417146305163212384832005924367753484871437731042165238964932920608988096746757585282365391701455222258919772283748442969489163122612874542328479985011793178437324509351503404273134948028573603448460822465,
    5224211491008373131406603536527981755345757742567201307027247664784412223361972085071271594280642689356776497337283996518196426296230388008390390705691353643411319840725993589925599219787596133403802269715179842,
    1255469150673352477643406441586559401886808227235272570913194477760462899397412967437903450228715079681927518702031385236882455686813595191144244687009073603134094899106009798791920033413388436982273752206346286,
)


A1 = (y1 ^ 2 - x1 ^ 3) - (y2 ^ 2 - x2 ^ 3)
A2 = (y1 ^ 2 - x1 ^ 3) - (y3 ^ 2 - x3 ^ 3)

# Factoring it
# print(A2 * (x1 - x2) - A1 * (x1 - x3))

# You can factor that by GMP-ECM with B1=1e5 and ~10000 iterations
# echo [COMPOSITE HERE] | ./ecm -c 10000 1e5
p = 223490196137382483691737269

assert (A1 * (x1 - x3) - A2 * (x1 - x2)) % p ^ K == 0
a = Mod(A1 / (x1 - x2), p ^ K).lift()
b = Mod(y1 ^ 2 - x1 ^ 3 - a * x1, p ^ K).lift()

E = EllipticCurve(Qp(p, prec=K), [a, b])
P = E(x1, y1)
Q = E(x2, y2)
R = E(x3, y3)

E0 = EllipticCurve(GF(p), [a, b])
N = E0.order()
ell = E.formal_group().log().polynomial()


def formal_log(P):
    return ell.subs(t=P[0] / P[1])

secret_key = ZZ(formal_log(N * Q) / formal_log(N * P))
print(bytes.fromhex(hex(Mod(x3 / secret_key, p ^ K).lift())[2:]))