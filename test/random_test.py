import random


def dist_test():
    #random.seed(42)

    n = 10**5

    seq = [random.choice([0,1]) for _ in xrange(n)]

    same = 6
    zero = [0 for _ in range(same)]
    count = 0
    rs = []
    for i, a in enumerate(seq[:-same-1]):
        if seq[i: i+same] == zero:
            rs.append(seq[i+same+1])
    print len(rs), sum(rs), sum(rs)*1.0/len(rs)

dist_test()
