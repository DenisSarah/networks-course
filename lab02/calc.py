import math

n = 60
p = 0.2

prob = 1 - sum(math.comb(n, k) * (p**k) * ((1 - p)**(n - k)) for k in range(12))

print(prob) # вывел 0.5513825262506507