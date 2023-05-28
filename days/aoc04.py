fmt_dict = {"sep": None}


def is_valid(n, span_func):
    n = str(n)
    if len(n) != 6:
        return False
    span = 1
    spans = set()
    for a, b in zip(n, n[1:]):
        if a > b:
            return False
        elif a == b:
            span += 1
        else:
            spans.add(span)
            span = 1
    spans.add(span)
    spans.discard(1)
    return span_func(spans)


def solve(data):
    a, b = map(int, data.split("-"))
    valid_passwords = set()
    valid_passwords_2 = set()
    for n in range(a, b + 1):
        if is_valid(n, lambda spans: 2 in spans):
            valid_passwords_2.add(n)
            valid_passwords.add(n)
        elif is_valid(n, lambda spans: spans):
            valid_passwords.add(n)
    return len(valid_passwords), len(valid_passwords_2)
