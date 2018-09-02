
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
gen_raw_nec_protocols = list(x+y for x in gen_raw_nec_protocols_standard for y in gen_raw_nec_protocols_suffixes)
def gen_raw_nec(protocol, device, subdevice, function):

    logical_bit  = 562.5

    protocol_base, protocol_suffix = (protocol.split('-') + [None])[:2]

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

    if protocol_base in ('nec1', 'necx1'):
        yield logical_bit * 16 # leading burst
    else:
        yield logical_bit * 8 # leading burst

    yield logical_bit *  -8 # space before data

    yield from encode(device)
    if subdevice >= 0:
        yield from encode(subdevice)
    else:
        yield from encode(~device)

    yield from encode(function & 0xFF)
    if protocol_suffix == 'y1':    # Yamaha special version 1
        yield from encode(function ^ 0x7F)
    elif protocol_suffix == 'y2':  # Yamaha special version 2
        yield from encode(function ^ 0xFE)
    elif protocol_suffix == 'y3':  # Yamaha special version 3
        yield from encode(function ^ 0x7E)
    elif protocol_suffix == 'f16': # 16 bit function
        yield from encode((function >> 8) & 0xFF) 
    else:                           # Standard invert
        yield from encode(function ^ 0xFF)

    yield logical_bit       # Trailing burst
    yield logical_bit * -3  # Trailing zero to separate


def gen_raw_general(protocol, device, subdevice, function, **kwargs):
    if protocol.lower() in gen_raw_nec_protocols:
        yield from gen_raw_nec(protocol.lower(), int(device), int(subdevice), int(function))


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
    l = len(c)
    yield from l.to_bytes(2, byteorder='little')
    yield from c
    yield from b'\x0d'
    yield from b'\x05'

    # calculate total length for padding
    l += 6 # header+len+trailer
    l += 4 # rm.send_data() 4 byte header (not seen here)
    yield from bytearray(16 - (l % 16))

def gen_hass_entityname(text):
    text = text.lower()
    text = text.replace(" ", "_")
    text = text.replace(":", "_")
    text = text.replace("+", "_plus_")
    text = text.replace("-", "_minus_")
    text = text.replace("__", "_")
    text = text.strip("_")
    return text

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate IR code')
    parser.add_argument('-i', dest='input', type=str,
                        required=True,
                        help='Input protocol',
                        choices=[*gen_raw_nec_protocols, 'raw', 'irdb', 'broadlink_base64'])
    parser.add_argument('-o', dest='output', type=str, 
                        required=True,
                        help='Output protocol',
                        choices=['broadlink', 'broadlink_hass', 'broadlink_base64', 'raw'])

    parser.add_argument('-d', dest='data',
                        nargs='+',
                        help='Data')

    parser.add_argument('-p', '--path', dest='path',
                        help='Device path used for irdb download')

    args = parser.parse_args()

    codes = []
    if args.input in 'irdb':
        import csv
        import requests

        base = 'http://cdn.rawgit.com/probonopd/irdb/master/codes'
        with requests.Session() as s:
            download = s.get('{}/{}'.format(base, args.path))
            content  = download.content.decode('utf-8')
            for row in csv.DictReader(content.splitlines(), delimiter=','):
                code = { 'functionname': row['functionname'],
                         'raw'         : gen_raw_general(**row) }
                codes.append(code)

    elif args.input == 'raw':
        code         = { 'functionname': 'raw',
                         'raw'         : args.data }
        codes.append(code)
    elif args.input == 'broadlink_base64':
        code         = { 'functionname': 'base64', 
                         'raw'         : gen_raw_from_broadlink_base64(args.data[0].encode()) }
        codes.append(code)
    else:
        code         = { 'functionname': '{}({})'.format(args.input, ','.join(map(str,args.data))),
                         'raw'         : gen_raw_general(args.input, *args.data) }
        codes.append(code)

    if args.output == 'broadlink':
        for r in codes:
            v = bytes(gen_broadlink_from_raw(code['raw']))
            print(v.hex())

    elif args.output == 'broadlink_base64':
        for r in codes:
            v = b64encode(bytes(gen_broadlink_from_raw(code['raw']))).decode()
            print(v)

    elif args.output == 'broadlink_hass':
        from base64      import b64encode
        from collections import OrderedDict
        from yaml        import dump, safe_dump

        group  = dict()
        group['entities'] = []
        for code in codes:
            group['entities'].append(gen_hass_entityname(code['functionname']))

        switch = dict()
        switch['switches'] = dict()
        for code in codes:
            v = bytes(gen_broadlink_from_raw(code['raw']))
            entity = dict()
            entity['command_on']  = b64encode(v).decode()
            entity['friendlyname'] = code['functionname']
            switch['switches'][gen_hass_entityname(code['functionname'])] = entity
        print(safe_dump(switch, allow_unicode=True, default_flow_style=False))
        print(safe_dump(group, allow_unicode=True, default_flow_style=False))



    elif args.output == 'raw':
        def signed(x):
            for v in x:
                if v > 0:
                    yield "+{}".format(v)
                else:
                    yield "{}".format(v)

        for code in codes:
            print(" ".join(signed(code['raw'])))

