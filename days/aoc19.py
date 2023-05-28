from collections import defaultdict
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


class TractorBeamGrid:
    def __init__(self, arr):
        self.__arr = arr
        self.__cpu = IntcodeComputer(arr, [])
        self.__beam = {}
        self.__N = 100
        self.__m1 = None
        self.__m2 = None

    def set_slopes(self, m1, m2):
        self.__m1 = m1
        self.__m2 = m2

    def is_in_beam(self, x, y):
        ret = self.__beam.get((x, y), None)
        if ret is not None:
            return ret
        self.__cpu = IntcodeComputer(self.__arr, [x, y])
        while self.__cpu.is_active():
            match self.__cpu.step():
                case StepResponse.PROVIDED_OUTPUT, ret:
                    self.__beam[x, y] = ret
                    return ret

    def __get_y_bounds(self, x):
        yl = int(x * self.__m1)
        if self.is_in_beam(x, yl):
            yl -= 1
            while self.is_in_beam(x, yl):
                yl -= 1
            yl += 1
        else:
            yl += 1
            while not self.is_in_beam(x, yl):
                yl += 1
        yh = int(x * self.__m2)
        if self.is_in_beam(x, yh):
            yh += 1
            while self.is_in_beam(x, yh):
                yh += 1
            yh -= 1
        else:
            yh -= 1
            while not self.is_in_beam(x, yh):
                yh -= 1
        self.__m1, self.__m2 = yl / x, yh / x
        return yl, yh

    def __square_fits(self, xl):
        _, yh = self.__get_y_bounds(xl)
        x0, x1, y0, y1 = xl, xl + self.__N - 1, yh - self.__N + 1, yh
        return all(
            self.is_in_beam(x, y) for x, y in ((x0, y0), (x0, y1), (x1, y1), (x1, y0))
        )

    def find_square(self):
        xl = int(self.__N / (self.__m2 - self.__m1))
        if self.__square_fits(xl):
            xl -= 1
            while self.__square_fits(xl):
                xl -= 1
            xl += 1
        else:
            xl += 1
            while not self.__square_fits(xl):
                xl += 1
        _, yh = self.__get_y_bounds(xl)
        return 10000 * xl + yh - self.__N + 1


def solve(data):
    arr = ints(data)
    grid = TractorBeamGrid(arr)
    ans1 = 0
    beam = defaultdict(set)
    N = 50
    for x in range(N):
        for y in range(N):
            if grid.is_in_beam(x, y):
                beam[x].add(y)
                ans1 += 1
    for x in range(N - 1, -1, -1):
        ys = beam[x]
        if ys and not {0, N - 1} & ys:
            grid.set_slopes(min(ys) / x, max(ys) / x)
            break
    return ans1, grid.find_square()
