
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
                        choices=['nec'])
    parser.add_argument('-o', '--output', dest='output', type=str, 
                        required=True,
                        help='Output type',
                        choices=['broadlink'])

    parser.add_argument('-d', '--device', dest='device',
                        required=True,
                        type=int,
                        help='Device')

    parser.add_argument('-s', '--subdevice', dest='subdevice',
                        required=True,
                        type=int,
                        help='Sub device')

    parser.add_argument('-c', '--command', dest='command',
                        required=True,
                        type=int,
                        help='Command')
    args = parser.parse_args()

    raw = []
    if args.input == 'nec':
        raw = gen_raw_nec2x(args.device, args.subdevice, args.command)


    if args.output == 'broadlink':
        v = bytes(gen_broadlink_from_raw(raw))
        print(v.hex())

    #v = list(gen_raw_nec2x(7, 7, 17))
    #print(v)

    #print(' '.join([str(int(x)) for x in v]))



    #v = bytes(gen_broadlink_from_raw(v))
    #print(v.hex())
    #print(binascii.hexlify(v))

    #print(bytes(gen_broadlink_from_raw([1000, -100])).hex())
    #print(bytes(gen_broadlink_from_raw([1000,  100])).hex())


    #print(list(simplify_raw([-1, 1, 2, -3, -1])))

    #d = [hex(int(i / 32.84)) for i in v]
    #print(d)
    #d = [hex(int(i * 269 / 8192)) for i in v]
    #print(d)
