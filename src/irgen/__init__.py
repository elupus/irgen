
from base64 import b64encode, b64decode
import binascii
from itertools import islice

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


def gen_raw_nec(protocol, device, subdevice, function):

    logical_bit = 562.5

    protocol_base, protocol_suffix = (protocol.split('-') + [None])[:2]

    def u8_to_bin(v):
        if(v < 0):
            v += (1 << 8)
        return bin(v)[2:].rjust(8, '0')

    def encode(value):
        b = u8_to_bin(value)
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
    yield value


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
            d = next(x)
            if d == 0:
                d = int.from_bytes(islice(x, 2), byteorder='big')

            yield sign * decode_one(d)
            sign = sign * -1

    yield from decode_iter(islice(v, length))


def gen_raw_from_broadlink_base64(data):
    yield from gen_raw_from_broadlink(b64decode(data))


def gen_broadlink_from_raw(data):
    yield from b'\x26'  # IR
    yield from b'\x00'  # Repeat

    def encode_one(x):
        # v = abs(int(i / 32.84))
        v = abs(int(x * 269 / 8192))
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
