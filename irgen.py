
from base64 import b64encode
import binascii



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

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate IR code')
    parser.add_argument('-i', dest='input', type=str,
                        required=True,
                        help='Input protocol',
                        choices=[*gen_raw_nec_protocols, 'raw', 'irdb'])
    parser.add_argument('-o', dest='output', type=str, 
                        required=True,
                        help='Output protocol',
                        choices=['broadlink', 'broadlink_hass', 'raw'])

    parser.add_argument('-d', dest='data',
                        type=int,
                        nargs='+',
                        help='Data')

    parser.add_argument('-p', '--path', dest='path',
                        help='Device path used for irdb download')

    args = parser.parse_args()

    raw = []
    if args.input in 'irdb':
        import csv
        import requests

        base = 'http://cdn.rawgit.com/probonopd/irdb/master/codes'
        with requests.Session() as s:
            download = s.get('{}/{}'.format(base, args.path))
            content  = download.content.decode('utf-8')
            for row in csv.DictReader(content.splitlines(), delimiter=','):
                ir = gen_raw_general(**row)
                code = (row['functionname'], gen_raw_general(**row))
                raw.append(code)

    elif args.input == 'raw':
        functionname = '{}({})'.format(args.input, ','.join(map(str,args.data)))
        code         = (functionname, args.data)
        raw.append(code)
    else:
        functionname = '{}({})'.format(args.input, ','.join(map(str,args.data)))
        data         = gen_raw_general(args.input, *args.data)
        code         = (functionname, data)
        raw.append(code)


    if args.output == 'broadlink':
        for r in raw:
            v = bytes(gen_broadlink_from_raw(r[1]))
            print(v.hex())

    if args.output == 'broadlink_hass':
        from base64      import b64encode
        from collections import OrderedDict
        from yaml        import dump, safe_dump


        switch = dict()
        switch['switches'] = dict()
        for r in raw:
            v = bytes(gen_broadlink_from_raw(r[1]))
            entity = dict()
            entity['command_on']  = b64encode(v).decode()
            switch['switches'][r[0]] = entity
        print(safe_dump(switch, allow_unicode=True, default_flow_style=False))

    elif args.output == 'raw':
        for r in raw:
            print(list(r[1]))

