from collections import defaultdict, deque


def solve(data):
    orbiting = {}
    for line in data:
        orbitee, orbiter = line.split(")")
        orbiting[orbiter] = orbitee
    scores = defaultdict(int)
    for orbiter, orbitee in orbiting.items():
        scores[orbitee] += 1
        while (orbitee := orbiting.get(orbitee, None)) is not None:
            scores[orbitee] += 1
    total_orbits = sum(scores.values())

    adjacencies = defaultdict(set)
    for orbiter, orbitee in orbiting.items():
        adjacencies[orbitee].add(orbiter)
        adjacencies[orbiter].add(orbitee)
    START = orbiting["YOU"]
    END = orbiting["SAN"]
    seen = {"YOU", "SAN", START}
    q = deque(((START, 0),))
    while q:
        node, transfers = q.popleft()
        if node == END:
            return total_orbits, transfers
        transfers += 1
        for adj in adjacencies[node]:
            if adj in seen:
                continue
            seen.add(adj)
            q.append((adj, transfers))
    return total_orbits, None
