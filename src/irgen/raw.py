

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


def paired(x):
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
        yield 0.0

def rtrim(x):
    """
    Simplify raw string.

    Drop negative trailers
    """
    def trimmer(y):
        y = iter(y)
        for z in y:
            if z <= 0:
                continue
            yield z
            break
        yield from y

    yield from reversed(list(trimmer(reversed(list(x)))))
