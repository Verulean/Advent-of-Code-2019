from collections import deque
from enum import IntEnum
from util import ints

fmt_dict = {"sep": None}
param_counts = {1: 3, 2: 3, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 1, 99: 0}


class StepResponse(IntEnum):
    SUCCESS = 0
    WAITING_FOR_INPUT = 1
    PROVIDED_OUTPUT = 2
    STOPPED = 3


class DroidResponse(IntEnum):
    WALL = 0
    MOVED = 1
    OXYGEN_SOURCE = 2


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


class OxygenFinder:
    def __init__(self, arr):
        self.__arr = arr

    def __simulate(self, commands):
        cpu = IntcodeComputer(self.__arr, [])
        inputs = list(commands)
        outputs = []
        while cpu.is_active():
            match cpu.step():
                case StepResponse.WAITING_FOR_INPUT:
                    if not inputs:
                        break
                    cpu.append_input(inputs.pop(0))
                case StepResponse.PROVIDED_OUTPUT, out_value:
                    outputs.append(out_value)
        return outputs

    def solve(self):
        walls = set()
        spaces = set()
        oxygen_source = None
        min_steps = None
        fill_time = 0

        # find the oxygen source and map the area
        q = deque()
        q.append((0, 0, tuple()))
        best_steps = {}
        best_steps[0, 0] = 0
        while q:
            i, j, path = q.popleft()
            for di, dj, inp in ((-1, 0, 1), (1, 0, 2), (0, -1, 3), (0, 1, 4)):
                ii, jj = i + di, j + dj
                if (ii, jj) in walls:
                    continue
                best = best_steps.get((ii, jj), None)
                if best is not None and best <= len(path) + 1:
                    continue
                new_path = path + (inp,)
                match self.__simulate(new_path)[-1]:
                    case DroidResponse.WALL:
                        walls.add((ii, jj))
                    case DroidResponse.MOVED:
                        n = len(new_path)
                        best_steps[(ii, jj)] = n
                        q.append((ii, jj, new_path))
                        spaces.add((ii, jj))
                    case DroidResponse.OXYGEN_SOURCE:
                        oxygen_source = ii, jj
                        min_steps = len(new_path)
                        spaces.add((ii, jj))

        # flood fill with oxygen
        seen = set()
        q.clear()
        q.append((*oxygen_source, 0))
        while q:
            i, j, t = q.popleft()
            t += 1
            for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ii, jj = i + di, j + dj
                if (ii, jj) in seen or (ii, jj) in walls or (ii, jj) not in spaces:
                    continue
                seen.add((ii, jj))
                q.append((ii, jj, t))
                fill_time = max(fill_time, t)

        return min_steps, fill_time


def solve(data):
    arr = ints(data)
    finder = OxygenFinder(arr)
    return finder.solve()
