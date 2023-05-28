from collections import defaultdict
from enum import Enum
from util import ints

fmt_dict = {"sep": None}
param_counts = {1: 3, 2: 3, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 1, 99: 0}
index_to_direction = [(-1, 0), (0, 1), (1, 0), (0, -1)]
direction_to_index = {(-1, 0): 0, (0, 1): 1, (1, 0): 2, (0, -1): 3}


def rotate(i, j, d):
    offset = 1 if d == 1 else -1
    return index_to_direction[(direction_to_index[i, j] + offset) % 4]


class StepResponse(Enum):
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


class HullPaintingRobot:
    def __init__(self, arr):
        self.__arr = arr
        self.__hull = defaultdict(int)
        self.reset()

    def reset(self, start_on_white=False):
        self.__cpu = IntcodeComputer(self.__arr, [])
        self.__i, self.__j, self.__di, self.__dj = 0, 0, -1, 0
        self.__hull.clear()
        if start_on_white:
            self.__hull[self.__i, self.__j] = 1

    def run(self):
        painting = True
        while self.__cpu.is_active():
            match self.__cpu.step():
                case StepResponse.WAITING_FOR_INPUT:
                    self.__cpu.append_input(self.__hull[self.__i, self.__j])
                case StepResponse.PROVIDED_OUTPUT, out_value:
                    if painting:
                        self.__hull[self.__i, self.__j] = out_value
                    else:
                        self.__di, self.__dj = rotate(self.__di, self.__dj, out_value)
                        self.__i += self.__di
                        self.__j += self.__dj
                    painting = not painting
        return len(self.__hull)

    @property
    def registration_identifier(self):
        whites = set()
        bounds = [None] * 4
        for (i, j), color in self.__hull.items():
            if color == 0:
                continue
            whites.add((i, j))
            if bounds[0] is None or i < bounds[0]:
                bounds[0] = i
            if bounds[1] is None or i > bounds[1]:
                bounds[1] = i
            if bounds[2] is None or j < bounds[2]:
                bounds[2] = j
            if bounds[3] is None or j > bounds[3]:
                bounds[3] = j
        return "\n".join(
            "".join(
                "#" if (i, j) in whites else "."
                for j in range(bounds[2], bounds[3] + 1)
            )
            for i in range(bounds[0], bounds[1] + 1)
        )


def solve(data):
    arr = ints(data)
    robot = HullPaintingRobot(arr)
    tiles_painted = robot.run()
    robot.reset(start_on_white=True)
    robot.run()
    return tiles_painted, robot.registration_identifier
