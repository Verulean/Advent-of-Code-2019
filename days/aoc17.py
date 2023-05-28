from enum import IntEnum
from util import ints

fmt_dict = {"sep": None}
param_counts = {1: 3, 2: 3, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 1, 99: 0}


class StepResponse(IntEnum):
    SUCCESS = 0
    WAITING_FOR_INPUT = 1
    PROVIDED_OUTPUT = 2
    STOPPED = 3


class Memory(list):
    def __getitem__(self, i):
        if i >= len(self):
            self.extend([0] * (i - len(self) + 1))
        return super().__getitem__(i)

    def __setitem__(self, i, v):
        if i >= len(self):
            self.extend([0] * (i - len(self) + 1))
        return super().__setitem__(i, v)


class IntcodeComputer:
    def __init__(self, arr, inputs):
        self.__i = 0
        self.__b = 0
        self.__arr = Memory(arr)
        self.__active = True
        self.__inputs = inputs

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

    @property
    def memory(self):
        return self.__arr

    def is_active(self):
        return self.__active

    def append_input(self, value):
        self.__inputs.append(value)

    def step(self):
        if not self.__active:
            return StepResponse.STOPPED
        op, modes = IntcodeComputer.parse_instruction(self.__arr[self.__i])
        params = []
        for di, mode in enumerate(modes):
            params.append(
                self.__arr[self.__arr[self.__i + di + 1]]
                if mode == 0  # position mode
                else self.__arr[self.__i + di + 1]
                if mode == 1  # absolute mode
                else self.__arr[self.__b + self.__arr[self.__i + di + 1]]
                if mode == 2  # relative mode
                else None
            )
        match op:
            case 1:  # add
                a, b, *_ = params
                self.__arr[
                    self.__arr[self.__i + 3] + (self.__b if modes[-1] == 2 else 0)
                ] = (a + b)
                self.__i += 4
            case 2:  # multiply
                a, b, *_ = params
                self.__arr[
                    self.__arr[self.__i + 3] + (self.__b if modes[-1] == 2 else 0)
                ] = (a * b)
                self.__i += 4
            case 3:  # input
                if len(self.__inputs) == 0:
                    return StepResponse.WAITING_FOR_INPUT
                self.__arr[
                    self.__arr[self.__i + 1] + (self.__b if modes[-1] == 2 else 0)
                ] = self.__inputs.pop(0)
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
                self.__arr[
                    self.__arr[self.__i + 3] + (self.__b if modes[-1] == 2 else 0)
                ] = (1 if params[0] < params[1] else 0)
                self.__i += 4
            case 8:  # equal to
                self.__arr[
                    self.__arr[self.__i + 3] + (self.__b if modes[-1] == 2 else 0)
                ] = (1 if params[0] == params[1] else 0)
                self.__i += 4
            case 9:  # relative base offset
                self.__b += params[0]
                self.__i += 2
            case 99:
                self.__active = False
                return StepResponse.STOPPED
            case _:
                raise ValueError()
        return StepResponse.SUCCESS


class ASCII:
    def __init__(self, arr):
        self.__arr = arr
        self.__cpu = IntcodeComputer(arr, [])
        self.__scaffolds = set()

    def render(self):
        self.__scaffolds.clear()
        i = 0
        j = -1
        while self.__cpu.is_active():
            match self.__cpu.step():
                case StepResponse.PROVIDED_OUTPUT, out_value:
                    j += 1
                    match out_value:
                        case 10:
                            i += 1
                            j = -1
                        case 35 | 60 | 62 | 94 | 118:
                            self.__scaffolds.add((i, j))

    def sweep_dust(self, movement_program):
        self.__cpu = IntcodeComputer(self.__arr, [ord(c) for c in movement_program])
        self.__cpu.memory[0] = 2
        total_dust = None
        while self.__cpu.is_active():
            match self.__cpu.step():
                case StepResponse.PROVIDED_OUTPUT, total_dust:
                    pass
                case StepResponse.STOPPED | StepResponse.WAITING_FOR_INPUT:
                    return total_dust

    def alignment_parameters(self):
        params = []
        for i, j in self.__scaffolds:
            if all(
                (ii, jj) in self.__scaffolds
                for ii, jj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1))
            ):
                params.append(i * j)
        return params


def solve(data):
    arr = ints(data)
    ascii = ASCII(arr)
    ascii.render()
    ans1 = sum(ascii.alignment_parameters())
    program = "\n".join(
        [
            "A,B,A,C,A,B,C,B,C,B",
            "R,10,R,10,R,6,R,4",
            "R,10,R,10,L,4",
            "R,4,L,4,L,10,L,10",
            "n",
            "",
        ]
    )
    return ans1, ascii.sweep_dust(program)
