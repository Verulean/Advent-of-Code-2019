from util import ints

fmt_dict = {"sep": None}
param_counts = {1: 3, 2: 3, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 99: 0}


def parse_instruction(n):
    n = str(n)
    op = int(n[-2:])
    i = len(n) - 3
    modes = []
    for _ in range(param_counts.get(op, 0)):
        if i >= 0:
            modes.append(int(n[i]))
            i -= 1
        else:
            modes.append(0)
    return op, modes


def simulate(arr, inputs):
    outputs = []
    arr = list(arr)
    i = 0
    n = len(arr)
    while i < n:
        op, modes = parse_instruction(arr[i])
        params = []
        for di, mode in enumerate(modes):
            params.append(arr[arr[i + di + 1]] if mode == 0 else arr[i + di + 1])
        match op:
            case 1:  # add
                a, b, *_ = params
                arr[arr[i + 3]] = a + b
                i += 4
            case 2:  # multiply
                a, b, *_ = params
                arr[arr[i + 3]] = a * b
                i += 4
            case 3:  # input
                arr[arr[i + 1]] = inputs.pop(0)
                i += 2
            case 4:  # output
                outputs.append(params[0])
                i += 2
            case 5:  # jump if true
                if params[0] != 0:
                    i = params[1]
                else:
                    i += 3
            case 6:  # jump if false
                if params[0] == 0:
                    i = params[1]
                else:
                    i += 3
            case 7:  # less than
                arr[arr[i + 3]] = 1 if params[0] < params[1] else 0
                i += 4
            case 8:  # equal to
                arr[arr[i + 3]] = 1 if params[0] == params[1] else 0
                i += 4
            case 99:
                break
            case _:
                raise ValueError()
    return outputs


def solve(data):
    arr = ints(data)
    return simulate(arr, [1])[-1], simulate(arr, [5])
