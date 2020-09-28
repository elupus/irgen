"""IR generator tool."""
from base64 import b64encode, b64decode, decode
from itertools import islice
from functools import wraps
import logging
from . import raw

LOG = logging.getLogger(__name__)

gen_raw_nec_protocols_standard = ['nec1',
                                  'nec2',
                                  'necx1',
                                  'necx2']
gen_raw_nec_protocols_suffixes = ['',
                                  '-y1',
                                  '-y2',
                                  '-y3',
                                  '-f16']

gen_raw_nec_protocols = list(x + y for x in gen_raw_nec_protocols_standard
                             for y in gen_raw_nec_protocols_suffixes)

gen_raw_rc5_protocols = ['rc5']

gen_raw_rc6_protocols = ['rc6']

gen_raw_rca38_protocols = ['rca38']

gen_raw_protocols = [
    *gen_raw_nec_protocols,
    *gen_raw_rc5_protocols,
    *gen_raw_rc6_protocols,
    *gen_raw_rca38_protocols
]


def uX_to_bin(v, x):
    """Create a binary set of valued."""
    if(v < 0):
        v += (1 << x)
    return bin(v)[2:].rjust(x, '0')


def bin_to_uX(v):
    return int("".join(v), 2)
 

def gen_bitified_from_raw(data, logical_bit):
    """Splits durations into bitified chunks"""
    for duration in data:
        bits = abs(round(duration / logical_bit))
        sign = 1 if duration > 0 else -1
        error = abs(duration) - logical_bit*bits
        if abs(error / logical_bit) > 0.1:
            raise Exception(f"Value {duration} with error {error} can't be cleanly decoded into bits of length {logical_bit}")
        for _ in range(bits):
            yield sign


def gen_raw_from_bitified(data, logical_bit):
    """Rescales output to logical bit length."""
    for bit in data:
        yield bit * logical_bit


def gen_raw_from_bitified_decorator(logical_bits):
    """Rescales output to logical bit length."""
    def inner_2(func):
        @wraps(func)
        def inner_1(*args, **kwargs):
            yield from gen_raw_from_bitified(func(*args, **kwargs), logical_bits)
        return inner_1
    return inner_2


@gen_raw_from_bitified_decorator(889.0)
def gen_raw_rc5(device, function, toggle):
    """Generate a raw list from rc5 parameters."""
    def encode_bit(s):
        if s == '1':
            yield -1
            yield 1
        else:
            yield 1
            yield -1

    def encode(x, l):
        for s in uX_to_bin(x, l):
            yield from encode_bit(s)

    yield from encode(1, 1)  # start
    if function < 64:
        yield from encode(1, 1)  # field (function 0-63)
    else:
        yield from encode(0, 1)  # field (function 64-127)
    yield from encode(toggle, 1)  # toggle

    # address
    yield from encode(device, 5)

    # command
    yield from encode(function % 64, 6)

    # trailing silence
    yield -100


def dec_raw_rc5(data):
    v = gen_bitified_from_raw(data, 889.0)

    def decode_bit(x):
        x1 = next(x)
        x2 = next(x)
        if x1 < 0 and x2 > 0:
            return '1'
        elif x1 > 0 and x2 < 0:
            return '0'
        else:
            raise Exception(f"Unexpected pair {x1} and {x2}")

    def decode(x, l):
        return bin_to_uX([decode_bit(x) for _ in range(l)])

    # look for start bit
    while next(v) == -1:
        pass

    function = decode_bit(v)
    toggle = decode_bit(v)
    address = decode(v, 5)
    command = decode(v, 6)

    if function == '0':
        command += 64

    # verify trailing silence
    try:
        for _ in range(100):
            assert next(v) == -1
    except StopIteration:
        pass

    return (address, command, int(toggle))


@gen_raw_from_bitified_decorator(444.0)
def gen_raw_rc6(device, function, toggle=0, mode=0):
    """Generate a raw list from rc6 parameters."""

    def encode_bit(s):
        if s == '1':
            yield 1
            yield -1
        else:
            yield -1
            yield 1

    def encode(x, l):
        for s in uX_to_bin(x, l):
            yield from encode_bit(s)

    # LS
    yield 6
    yield -2

    # SB
    yield from encode(1, 1)

    # Mode
    yield from encode(mode, 3)

    # TB
    if toggle:
        yield 2
        yield -2
    else:
        yield -2
        yield 2

    # Control
    yield from encode(device, 8)

    # Information
    yield from encode(function, 8)

    # Signal Free
    yield -6


def dec_raw_rc6(data):

    def decode_bit(x):
        x1 = next(x)
        x2 = next(x)
        if x1 < 0 and x2 > 0:
            return '0'
        elif x1 > 0 and x2 < 0:
            return '1'
        else:
            raise Exception(f"Unexpected pair {x1} and {x2}")

    def decode(x, l):
        return bin_to_uX([decode_bit(x) for _ in range(l)])

    v = gen_bitified_from_raw(data, 444.0)

    # LS
    while next(v) == -1:
        pass
    for _ in range(5):
        assert next(v) == 1
    for _ in range(2):
        assert next(v) == -1

    sb = decode_bit(v)
    assert sb == '1'

    mode = decode(v, 3)
    toggle_raw = [next(v) for _ in range(4)]
    if toggle_raw == [1, 1, -1, -1]:
        toggle = 1
    elif toggle_raw == [-1, -1, 1, 1]:
        toggle = 0
    else:
        raise Exception(f"Unexpected toggle {toggle_raw}")

    device = decode(v, 8)
    function = decode(v, 8)

    # verify trailing silence
    try:
        for _ in range(6):
            assert next(v) == -1
    except StopIteration:
        pass

    return (device, function, toggle, mode)


@gen_raw_from_bitified_decorator(562.5)
def gen_raw_nec(protocol, device, subdevice, function):
    """Generate a raw list from nec parameters."""
    protocol_base, protocol_suffix = (protocol.split('-') + [None])[:2]

    def encode_bit(s):
        yield 1  # burst
        if s == '1':
            yield -3  # one  is encoded by 3 length
        else:
            yield -1  # zero is encoded by 1 lengths

    def encode(value):
        b = uX_to_bin(value, 8)
        for s in reversed(b):
            yield from encode_bit(s)

    if protocol_base in ('nec1', 'necx1'):
        yield 16  # leading burst
    else:
        yield 8   # leading burst

    yield -8      # space before data

    yield from encode(device)
    if subdevice >= 0:
        yield from encode(subdevice)
    else:
        yield from encode(~device)

    yield from encode(function & 0xFF)
    if protocol_suffix == 'y1':     # Yamaha special version 1
        yield from encode(function ^ 0x7F)
    elif protocol_suffix == 'y2':   # Yamaha special version 2
        yield from encode(function ^ 0xFE)
    elif protocol_suffix == 'y3':   # Yamaha special version 3
        yield from encode(function ^ 0x7E)
    elif protocol_suffix == 'f16':  # 16 bit function
        yield from encode((function >> 8) & 0xFF)
    else:                           # Standard invert
        yield from encode(function ^ 0xFF)

    yield 1   # Trailing burst
    yield -3  # Trailing zero to separate


@gen_raw_from_bitified_decorator(460.0)
def gen_raw_rca38(device, function):
    """Generate a raw list from rca38 parameters."""

    def encode_bit(s):
        if s == '1':
            yield 1
            yield -4
        else:
            yield 1
            yield -2

    def rev_encode_bit(s):
        if s == '1':
            yield from encode_bit('0')
        else:
            yield from encode_bit('1')

    def encode(x, l, f):
        for s in uX_to_bin(x, l):
            yield from f(s)

    # Starting burst
    yield 8
    yield -8

    # Device and function
    yield from encode(device, 4, encode_bit)
    yield from encode(function, 8, encode_bit)

    # Reversed device and function
    yield from encode(device, 4, rev_encode_bit)
    yield from encode(function, 8, rev_encode_bit)

    # Ending burst
    yield 1
    yield -16


def gen_raw_general(protocol, device, subdevice, function, **kwargs):
    if protocol.lower() in gen_raw_nec_protocols:
        yield from gen_raw_nec(protocol.lower(),
                               int(device),
                               int(subdevice),
                               int(function))

    if protocol.lower() in gen_raw_rc5_protocols:
        yield from gen_raw_rc5(device=int(device),
                               function=int(function),
                               toggle=kwargs.get("toggle", 0))

    if protocol.lower() in gen_raw_rc6_protocols:
        yield from gen_raw_rc6(device=int(device),
                               function=int(function),
                               toggle=kwargs.get("toggle", 0),
                               mode=kwargs.get("mode", 0))

    if protocol.lower() in gen_raw_rca38_protocols:
        yield from gen_raw_rca38(device=int(device),
                                 function=int(function))


def gen_raw_from_broadlink(data):
    """Genearate raw values from broadling data."""
    v = iter(data)
    code = next(v)
    next(v)  # repeat

    assert code == 0x26  # IR

    length = int.from_bytes(islice(v, 2), byteorder='little')
    assert length >= 3  # a At least trailer
 
    def decode_one(x):
        return round(x * 8192 / 269, 0)

    def decode_iter(x):
        sign = 1
        while True:
            try:
                d = next(x)
            except StopIteration:
                return
            if d == 0:
                d = int.from_bytes(islice(x, 2), byteorder='big')
            
            yield sign * decode_one(d)
            sign = sign * -1
    
    yield from decode_iter(islice(v, length))

    rem = list(v)
    if any(rem):
        LOG.warning("Ignored extra data: %s", rem)


def gen_raw_from_broadlink_base64(data):
    """Generate raw data from a base 64 encoded broadlink data."""
    yield from gen_raw_from_broadlink(b64decode(data))


def gen_broadlink_from_raw(data, repeat=0):
    """Generate broadlink datat from a raw values."""
    yield from b'\x26'  # IR
    yield from repeat.to_bytes(1, byteorder='big')  # Repeat

    # all broadlink ir captures will end with
    # 0x00 0x0d 0x05, which is just a long
    # trailing silence in the command set.
    # On generation we just need to ensure
    # our data ends with silence.
    trailing_silience = -101502.0

    def encode_one(x):
        # v = abs(int(i / 32.84))
        v = abs(round(x * 269 / 8192))
        if v > 255:
            yield from b'\x00'
            yield from v.to_bytes(2, byteorder='big')
        else:
            yield from v.to_bytes(1, byteorder='big')

    def encode_list(x):
        for i in raw.paired(raw.simplify(x), trailing_silience):
            yield from encode_one(i)

    c = bytearray(encode_list(data))
    count = len(c)
    yield from count.to_bytes(2, byteorder='little')
    yield from c

    # calculate total length for padding
    count += 4  # header+len+trailer
    count += 4  # rm.send_data() 4 byte header (not seen here)
    if count % 16:
        yield from bytearray(16 - (count % 16))


def gen_broadlink_base64_from_raw(data, repeat=0):
    """Generate broadlink base64 encoded from raw data."""
    return b64encode(bytes(gen_broadlink_from_raw(data, repeat)))


def gen_raw_from_pronto(data):
    """Generate raw values from a pronto pair list."""
    clock = 0.241246  # Pronto clock base: 1000000 / (32768 * 506 / 4)

    v = iter(data)
    zero = next(v)
    assert zero == 0
    base = next(v)
    freq = 1.0 / (base * clock)

    seq1_len = next(v)
    seq2_len = next(v)

    for _ in range(seq1_len):
        yield +round(next(v) / freq, 1)
        yield -round(next(v) / freq, 1)

    for _ in range(seq2_len):
        yield +round(next(v) / freq, 1)
        yield -round(next(v) / freq, 1)


def gen_pronto_from_raw_int(seq1, seq2, base=None, freq=None):
    """Generate pronto pair ints from raw."""
    clock = 0.241246  # Pronto clock base: 1000000 / (32768 * 506 / 4)

    if freq is None:
        if base is None:
            freq = 0.040
        else:
            freq = 1.0 / (base * clock)

    if base is None:
        base = int(1 / (freq * clock))

    yield 0
    yield base

    def fixup(x):
        return list(raw.paired(raw.simplify(x)))

    simple1 = fixup(seq1)
    simple2 = fixup(seq2)

    yield int(len(simple1)/2)  # sequence 1
    yield int(len(simple2)/2)  # sequence 2

    for x in simple1:
        yield int(abs(x) * freq)

    for x in simple2:
        yield int(abs(x) * freq)


def gen_pronto_from_raw(seq1, seq2, base=None, freq=None):
    """Generate pronto pair list from raw."""
    data = gen_pronto_from_raw_int(seq1, seq2, base, freq)
    for value in data:
        yield "{0:0{1}x}".format(value, 4)


dec_raw_protocols = {
    'rc5': dec_raw_rc5,
    'rc6': dec_raw_rc6,
}
