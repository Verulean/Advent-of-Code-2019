import numpy as np

fmt_dict = {"cast": int}


def solve(data):
    arr = np.array(data)
    ans1 = np.sum(arr // 3) - 2 * arr.size
    ans2 = 0
    for n in arr:
        while n > 8:
            n = n // 3 - 2
            ans2 += n
    return ans1, ans2
