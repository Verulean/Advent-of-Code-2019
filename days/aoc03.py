from collections import Counter


def wire_positions(wire):
    positions = {}
    i, j, d = 0, 0, 0
    for instr in wire:
        steps = int(instr[1:])
        match instr[0]:
            case "L":
                for _ in range(steps):
                    j -= 1
                    d += 1
                    if (i, j) not in positions:
                        positions[i, j] = d
            case "R":
                for _ in range(steps):
                    j += 1
                    d += 1
                    if (i, j) not in positions:
                        positions[i, j] = d
            case "U":
                for _ in range(steps):
                    i -= 1
                    d += 1
                    if (i, j) not in positions:
                        positions[i, j] = d
            case "D":
                for _ in range(steps):
                    i += 1
                    d += 1
                    if (i, j) not in positions:
                        positions[i, j] = d
    return positions


def solve(data):
    wires = [w.split(",") for w in data]
    overlaps = Counter()
    steps = Counter()

    for wire in wires:
        p = wire_positions(wire)
        overlaps.update(p.keys())
        steps.update(p)

    min_manhattan = None
    min_steps = None
    for (i, j), wire_count in overlaps.items():
        if wire_count < 2:
            continue

        dist_manhattan = abs(i) + abs(j)
        if min_manhattan is None or dist_manhattan < min_manhattan:
            min_manhattan = dist_manhattan

        dist_steps = steps[i, j]
        if min_steps is None or dist_steps < min_steps:
            min_steps = dist_steps

    return min_manhattan, min_steps
