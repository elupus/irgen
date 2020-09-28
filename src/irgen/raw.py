

def simplify(x):
    """
    Simplify raw string.

    Combine successive same sign value, drop zeros, drop leading negative
    """
    value = 0
    for i in x:
        if i == 0:
            continue
        elif value == 0:
            if i > 0:
                value = i
            else:
                pass  # leading negative
        elif (value > 0) == (i > 0):
            value += i
        else:
            yield value
            value = i
    if value != 0:
        yield value


def paired(x, silence=0):
    """Create pairs of on, off."""
    sign = 1
    for i in x:
        if (i < 0) ^ (sign < 0):
            yield 0.0
            yield i
        else:
            yield i
            sign = -sign
    if sign < 0:
        yield silence


def ltrim(x):
    """Drop leading silence"""
    x = iter(x)
    for y in x:
        if y <= 0:
            continue
        yield y
        break
    yield from x


def rtrim(x):
    """Drop trailing silence"""
    yield from reversed(list(ltrim(reversed(list(x)))))
