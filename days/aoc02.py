from util import ints

fmt_dict = {"sep": None}


def simulate(arr, noun=12, verb=2):
    arr = list(arr)
    arr[1], arr[2] = noun, verb
    i = 0
    n = len(arr)
    while i < n:
        match arr[i]:
            case 1:
                a, b, c = arr[i + 1 : i + 4]
                arr[c] = arr[a] + arr[b]
            case 2:
                a, b, c = arr[i + 1 : i + 4]
                arr[c] = arr[a] * arr[b]
            case _:
                break
        i += 4
    return arr[0]


def solve(data):
    arr = ints(data)
    ans1 = simulate(arr)
    for i in range(100):
        for j in range(100):
            if simulate(arr, i, j) == 19690720:
                return ans1, 100 * i + j
    return ans1, None
