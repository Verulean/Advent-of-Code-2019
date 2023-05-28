from collections import defaultdict
from enum import IntEnum
from util import ints

fmt_dict = {"sep": None}
param_counts = {1: 3, 2: 3, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 1, 99: 0}
index_to_direction = [(-1, 0), (0, 1), (1, 0), (0, -1)]
direction_to_index = {(-1, 0): 0, (0, 1): 1, (1, 0): 2, (0, -1): 3}
tiles = [" ", "#", ".", "_", "O"]


def rotate(i, j, d):
    offset = 1 if d == 1 else -1
    return index_to_direction[(direction_to_index[i, j] + offset) % 4]


class StepResponse(IntEnum):
    SUCCESS = 0
    WAITING_FOR_INPUT = 1
    PROVIDED_OUTPUT = 2
    STOPPED = 3


class OutputValue(IntEnum):
    X = 0
    Y = 1
    TILE_ID = 2


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


class ArcadeCabinet:
    def __init__(self, arr):
        self.__arr = arr
        self.__screen = defaultdict(int)
        self.reset()

    def reset(self, playable=False):
        self.__cpu = IntcodeComputer(self.__arr, [])
        if playable:
            self.__cpu.memory[0] = 2
        self.__screen.clear()
        self.score = 0
        self.__paddle_x = None
        self.__ball_x = None

    def run(self):
        expected_value = OutputValue.X
        x, y = None, None
        while self.__cpu.is_active():
            match self.__cpu.step():
                case StepResponse.WAITING_FOR_INPUT:
                    if self.__paddle_x == self.__ball_x:
                        self.__cpu.append_input(0)
                    elif self.__paddle_x > self.__ball_x:
                        self.__cpu.append_input(-1)
                    else:
                        self.__cpu.append_input(1)
                    self.__screen.clear()
                case StepResponse.PROVIDED_OUTPUT, out_value:
                    match expected_value:
                        case OutputValue.X:
                            x = out_value
                            expected_value = OutputValue.Y
                        case OutputValue.Y:
                            y = out_value
                            expected_value = OutputValue.TILE_ID
                        case OutputValue.TILE_ID:
                            if x == -1 and y == 0:
                                self.score = out_value
                            else:
                                self.__screen[y, x] = out_value
                                if out_value == 3:
                                    self.__paddle_x = x
                                elif out_value == 4:
                                    self.__ball_x = x
                            expected_value = OutputValue.X

    def __get_bounds(self):
        bounds = [None] * 4
        for y, x in self.__screen:
            if bounds[0] is None or y < bounds[0]:
                bounds[0] = y
            if bounds[1] is None or y > bounds[1]:
                bounds[1] = y
            if bounds[2] is None or x < bounds[2]:
                bounds[2] = x
            if bounds[3] is None or x > bounds[3]:
                bounds[3] = x
        return bounds

    @property
    def block_count(self):
        return sum(tile == 2 for tile in self.__screen.values())

    @property
    def screen(self):
        bounds = self.__get_bounds()
        return "\n".join(
            "".join(tiles[self.__screen[y, x]] for x in range(bounds[2], bounds[3] + 1))
            for y in range(bounds[0], bounds[1] + 1)
        )


def solve(data):
    arr = ints(data)
    cabinet = ArcadeCabinet(arr)
    cabinet.run()
    starting_block_count = cabinet.block_count
    cabinet.reset(playable=True)
    cabinet.run()
    return starting_block_count, cabinet.score
