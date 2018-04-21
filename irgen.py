
from base64 import b64encode
import binascii


def gen_raw_nec2x(device, subdevice, obc):

    logical_bit  = 562.5

    def u8_to_bin(v):
        if(v < 0):
            v += (1 << 8)
        return bin(v)[2:].rjust(8, '0')

    def encode(value):
        b = u8_to_bin(value)
        for s in reversed(b):
            yield logical_bit # burst
            if s == '1': yield logical_bit * -3 # one  is encoded by 3 length
            else:        yield logical_bit * -1 # zero is encoded by 1 lengths


    yield logical_bit *  -16 # leading burst
    yield logical_bit *  -8 # space before data

    yield from encode(device)
    yield from encode(subdevice)
    yield from encode(obc)
    yield from encode(~obc)
    yield logical_bit       # Trailing burst
    yield logical_bit * -3  # Trailing zero to separate


# combine successive same sign value, drop zeros, drop leading negative
def gen_simplified_from_raw(x):
    l = 0
    for i in x:
        if i == 0:
            continue
        elif l == 0:
            if i > 0:                
                l = i
            else:
                pass # leading negative
        elif (l > 0) == (i > 0):
            l += i
        else:
            yield l
            l = i
    yield l


def gen_broadlink_from_raw(data):
    yield from b'\x26' #IR
    yield from b'\x00' #Repeat

    def encode_one(x):
        #v = abs(int(i / 32.84))
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
    yield from len(c).to_bytes(2, byteorder='little')
    yield from c
    yield from b'\x0d'
    yield from b'\x05'


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate IR code')
    parser.add_argument('-i', '--input', dest='input', type=str,
                        required=True,
                        help='Input type',
                        choices=['nec', 'raw'])
    parser.add_argument('-o', '--output', dest='output', type=str, 
                        required=True,
                        help='Output type',
                        choices=['broadlink', 'raw'])

    parser.add_argument('-d', '--data', dest='data',
                        required=True,
                        type=int,
                        nargs='+',
                        help='Data')

    args = parser.parse_args()

    if args.input == 'nec':
        raw = gen_raw_nec2x(*args.data)
    if args.input == 'raw':
        raw = args.data

    if args.output == 'broadlink':
        v = bytes(gen_broadlink_from_raw(raw))
        print(v.hex())
    elif args.output == 'raw':
        print(list(raw))

