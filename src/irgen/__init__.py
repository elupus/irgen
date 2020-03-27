
from base64 import b64encode, b64decode
import binascii
from itertools import islice
import logging

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

gen_raw_protocols = [*gen_raw_nec_protocols, *gen_raw_rc5_protocols, *gen_raw_rc6_protocols]

def uX_to_bin(v, x):
    if(v < 0):
        v += (1 << x)
    return bin(v)[2:].rjust(x, '0')

def gen_raw_rc5(protocol, device, subdevice, function, toggle=0):
    logical_bit = 889.0

    def encode_bit(s):
        if s == '1':
            yield logical_bit * -1
            yield logical_bit * 1
        else:
            yield logical_bit * 1
            yield logical_bit * -1

    def encode_uX(x, l):
        for s in uX_to_bin(x, l):
            yield from encode_bit(s)

    yield from encode_bit('1')  # start
    if function < 64:
        yield from encode_bit('1')  # field (function 0-63)
    else:
        yield from encode_bit('0')  # field (function 64-127)
    yield from encode_bit(str(toggle))  # toggle

    # address
    yield from encode_uX(device, 5)

    # command
    yield from encode_uX(function % 64, 6)

    # trailing silence
    yield logical_bit * -100

def gen_raw_rc6(protocol, device, subdevice, function, toggle=0, mode=0):
    logical_bit = 444.0

    def encode_bit(s):
        if s == '1':
            yield logical_bit * 1
            yield logical_bit * -1
        else:
            yield logical_bit * -1
            yield logical_bit * 1

    def encode_uX(x, l):
        for s in uX_to_bin(x, l):
            yield from encode_bit(s)

    #LS
    yield logical_bit *  6
    yield logical_bit * -2

    #SB
    yield from encode_bit('1')

    #Mode
    yield from encode_uX(mode, 3)

    #TB
    if toggle:
        yield logical_bit *  2
        yield logical_bit * -2
    else:
        yield logical_bit * -2
        yield logical_bit *  2

    #Control
    yield from encode_uX(device, 8)

    #Information
    yield from encode_uX(function, 8)

    #Signal Free
    yield logical_bit * -6


def gen_raw_nec(protocol, device, subdevice, function):

    logical_bit = 562.5

    protocol_base, protocol_suffix = (protocol.split('-') + [None])[:2]

    def encode(value):
        b = uX_to_bin(value, 8)
        for s in reversed(b):
            yield logical_bit  # burst
            if s == '1':
                yield logical_bit * -3  # one  is encoded by 3 length
            else:
                yield logical_bit * -1  # zero is encoded by 1 lengths

    if protocol_base in ('nec1', 'necx1'):
        yield logical_bit * 16  # leading burst
    else:
        yield logical_bit * 8   # leading burst

    yield logical_bit * -8     # space before data

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

    yield logical_bit       # Trailing burst
    yield logical_bit * -3  # Trailing zero to separate


def gen_raw_general(protocol, device, subdevice, function, **kwargs):
    if protocol.lower() in gen_raw_nec_protocols:
        yield from gen_raw_nec(protocol.lower(),
                               int(device),
                               int(subdevice),
                               int(function))

    if protocol.lower() in gen_raw_rc5_protocols:
        yield from gen_raw_rc5(protocol.lower(),
                               int(device),
                               int(subdevice),
                               int(function))

    if protocol.lower() in gen_raw_rc6_protocols:
        yield from gen_raw_rc6(protocol.lower(),
                               int(device),
                               int(subdevice),
                               int(function))


def gen_simplified_from_raw(x):
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

def gen_paired_from_raw(x):
    """
    Create pairs of on, off
    """

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

def gen_raw_from_broadlink(data):
    v = iter(data)
    code = next(v)
    repeat = next(v)

    assert code == 0x26  # IR

    length = int.from_bytes(islice(v, 2), byteorder='little')

    def decode_one(x):
        return round(x * 8192 / 269)

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

    assert next(v) == 0x0d
    assert next(v) == 0x05

    rem = list(v)
    if any(rem):
        LOG.warning("Ignored extra data: %s", rem)


def gen_raw_from_broadlink_base64(data):
    yield from gen_raw_from_broadlink(b64decode(data))


def gen_broadlink_from_raw(data, repeat=0):
    yield from b'\x26'  # IR
    yield from repeat.to_bytes(1, byteorder='big')  # Repeat

    def encode_one(x):
        # v = abs(int(i / 32.84))
        v = abs(round(x * 269 / 8192))
        if v > 255:
            yield from b'\x00'
            yield from v.to_bytes(2, byteorder='big')
        else:
            yield from v.to_bytes(1, byteorder='big')

    def encode_list(x):
        for i in gen_simplified_from_raw(x):
            yield from encode_one(i)

    c = bytearray(encode_list(data))
    count = len(c)
    yield from count.to_bytes(2, byteorder='little')
    yield from c
    yield from b'\x0d'
    yield from b'\x05'

    # calculate total length for padding
    count += 6  # header+len+trailer
    count += 4  # rm.send_data() 4 byte header (not seen here)
    yield from bytearray(16 - (count % 16))


def gen_broadlink_base64_from_raw(data, repeat=0):
    return b64encode(bytes(gen_broadlink_from_raw(data, repeat)))


def gen_raw_from_pronto(data):
    clock = 0.241246 #  Pronto clock base: 1000000 / (32768 * 506 / 4)

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
    clock = 0.241246 #  Pronto clock base: 1000000 / (32768 * 506 / 4)

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
        return list(gen_paired_from_raw(gen_simplified_from_raw(x)))
        #return list(gen_paired_from_raw((x)))

    simple1 = fixup(seq1)
    simple2 = fixup(seq2)

    yield int(len(simple1)/2)  # sequence 1
    yield int(len(simple2)/2)  # sequence 2

    for x in simple1:
        yield int(abs(x) * freq)

    for x in simple2:
        yield int(abs(x) * freq)


def gen_pronto_from_raw(seq1, seq2, base=None, freq=None):
    data = gen_pronto_from_raw_int(seq1, seq2, base, freq)
    for value in data:
        yield "{0:0{1}x}".format(value,4)