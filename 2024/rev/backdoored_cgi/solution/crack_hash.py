import heapq

def factor(n):
  res = getoutput("factor {}".format(n))
  return list(map(int, res.split(': ')[1].split(' ')))

H = 0xfeedface

S = []
for i in range(32, 256):
  if i == 0x7f:
    continue
  S.append(i)

route = { H : [] }
mind = { H : 0 }

q = [(0, H)]
heapq.heapify(q)
print(q)

minv = H

cnt = 0
while q:
  d, v = heapq.heappop(q)
  minv = min(minv, v)

  # already updated. should not consider this path
  if mind[v] < d:
    continue

  if cnt % 100 == 0:
    print(cnt, len(q), hex(minv), d, hex(v), len(route[v]))

  if v == 1:
    print("Found!!!!")
    print(v, route[v])
    break

  for i in range(0xff):
    t = v + (i << 32)
    for j in S:
      if t % j == 0:
        nxt = t // j
        if (nxt >> 32) > 0:
          continue

        nd = d + (i != 0)
        if not nxt in mind or mind[nxt] > nd:
          route[nxt] = route[v] + [j]
          mind[nxt] = nd
          heapq.heappush(q, (nd, nxt))

  cnt += 1
