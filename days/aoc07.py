from enum import Enum
from itertools import permutations
from util import ints

fmt_dict = {"sep": None}
param_counts = {1: 3, 2: 3, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 99: 0}


class StepResponse(Enum):
    SUCCESS = 0
    WAITING_FOR_INPUT = 1
    PROVIDED_OUTPUT = 2
    STOPPED = 3


class Amplifier:
    def __init__(self, arr, phase):
        self.__i = 0
        self.__arr = list(arr)
        self.__active = True
        self.__inputs = [phase]

    @staticmethod
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

    def is_active(self):
        return self.__active

    def append_input(self, value):
        self.__inputs.append(value)

    def step(self):
        if not self.__active:
            return StepResponse.STOPPED
        op, modes = Amplifier.parse_instruction(self.__arr[self.__i])
        params = []
        for di, mode in enumerate(modes):
            params.append(
                self.__arr[self.__arr[self.__i + di + 1]]
                if mode == 0
                else self.__arr[self.__i + di + 1]
            )
        match op:
            case 1:  # add
                a, b, *_ = params
                self.__arr[self.__arr[self.__i + 3]] = a + b
                self.__i += 4
            case 2:  # multiply
                a, b, *_ = params
                self.__arr[self.__arr[self.__i + 3]] = a * b
                self.__i += 4
            case 3:  # input
                if len(self.__inputs) == 0:
                    return StepResponse.WAITING_FOR_INPUT
                self.__arr[self.__arr[self.__i + 1]] = self.__inputs.pop(0)
                self.__i += 2
            case 4:  # output
                self.__i += 2
                return StepResponse.PROVIDED_OUTPUT, params[0]
            case 5:  # jump if true
                if params[0] != 0:
                    self.__i = params[1]
                else:
                    self.__i += 3
            case 6:  # jump if false
                if params[0] == 0:
                    self.__i = params[1]
                else:
                    self.__i += 3
            case 7:  # less than
                self.__arr[self.__arr[self.__i + 3]] = 1 if params[0] < params[1] else 0
                self.__i += 4
            case 8:  # equal to
                self.__arr[self.__arr[self.__i + 3]] = (
                    1 if params[0] == params[1] else 0
                )
                self.__i += 4
            case 99:
                self.__active = False
                return StepResponse.STOPPED
            case _:
                raise ValueError()
        return StepResponse.SUCCESS


def simulate(arr, phases, next_amp):
    amps = [Amplifier(arr, phase) for phase in phases]
    amps[0].append_input(0)
    active_amp = 0
    out_value = None
    while active_amp is not None:
        match amps[active_amp].step():
            case StepResponse.PROVIDED_OUTPUT, out_value:
                active_amp = next_amp(amps, active_amp)
                if active_amp is None:
                    break
                amps[active_amp].append_input(out_value)
            case StepResponse.STOPPED | StepResponse.WAITING_FOR_INPUT:
                active_amp = next_amp(amps, active_amp)
    return out_value


def solve(data):
    arr = ints(data)

    def next_v1(amps, i):
        ii = i + 1
        return ii if ii < len(amps) else None

    def next_v2(amps, i):
        n = len(amps)
        for ii in range(i + 1, i + n):
            ii %= n
            if amps[ii].is_active():
                return ii
        return None

    return tuple(
        max(simulate(arr, p, next_func) for p in permutations(phases))
        for next_func, phases in ((next_v1, range(5)), (next_v2, range(5, 10)))
    )
