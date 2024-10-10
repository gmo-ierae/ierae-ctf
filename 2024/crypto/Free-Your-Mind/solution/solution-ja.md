流石に軽く説明がないと厳しい気がしたので, 解説を付しておきます. 

ランダムシードは特に意味ありません. ただのmislead. また, RSA自体を攻撃するわけではありません.

目的はノルム操作. とはいえ適当に選んでいたのではまともに動かない(適当に試せばわかりますが, ノルムは死ぬほどデカくなります)ので, e = 1みたいな特別な値にすることを目標にすることはほぼ自明になります. しかし簡単に探索可能な範囲は除外されています. 

$K := \mathbb{Q}$とおき, $\zeta$を1の原始11乗根とします. そして $L := K(\zeta^2 + \zeta^{-2})$ にします. この値はGaussian periodに合わせた程度しか理由はありません.

体論の基本的な結果から, $L/K$は有限次Galois拡大となり, $\lbrack L : K\rbrack = 5$です. 特にこれは巡回拡大になります. さてGalois拡大のとき「ノルムが1になる」といえばHilbertの定理90ですね. ということで, 定理の主張 $N_{L/K}(\alpha) = 1 \implies \exists \beta\in L.\ \alpha = \beta / \sigma(\beta)$ ( $\sigma\in\mathrm{Gal}(L/K)$ は生成元であるものとします)より, この $\beta$ を具体的に構成できれば勝ちということです. 

具体的な構成の前に, これが一種のDiophantine equationとして解釈できることに注意しましょう. すると先行研究がいくらか見えてきます.  たとえばElkies御大の[1]やその発展形である[2]です. これらはそこそこ具体的な手続きのみを記述しているため, 少々一般化して任意のノルムに対して適用できるようにしたものがsolve.sageです. 


## References
1. Noam D. Elkies. ***Pythagorean triples and Hilbert's Theorem 90***. https://abel.math.harvard.edu/~elkies/Misc/hilbert.pdf
2. Shin-ichi KATAYAMA. 2014. ***Diophantine Equations and Hilbert's Theorem 90***. https://repo.lib.tokushima-u.ac.jp/files/public/10/106352/20170929144755217956/LID201505145004.pdf

