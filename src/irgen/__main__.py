import irgen
from . import raw

def gen_hass_entityname(text):
    text = text.lower()
    text = text.replace(" ", "_")
    text = text.replace(":", "_")
    text = text.replace("+", "_plus_")
    text = text.replace("-", "_minus_")
    text = text.replace("__", "_")
    text = text.strip("_")
    return text


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate IR code')
    parser.add_argument('-i', dest='input', type=str,
                        required=True,
                        help='Input protocol',
                        choices=[*irgen.gen_raw_protocols,
                                 'raw',
                                 'irdb',
                                 'broadlink',
                                 'broadlink_base64',
                                 'pronto'])
    parser.add_argument('-o', dest='output', type=str,
                        required=True,
                        help='Output protocol',
                        choices=[*irgen.dec_raw_protocols.keys(),
                                 'broadlink',
                                 'broadlink_base64',
                                 'raw',
                                 'pronto'])
    parser.add_argument('-r', dest='repeats',
                              help='Number of repeats',
                              default=1,
                              type=int)

    parser.add_argument('-d', dest='data',
                        nargs='+',
                        help='Data')

    parser.add_argument('-p', '--path', dest='path',
                        help='Device path used for irdb download')

    args = parser.parse_args()

    codes = []

    # Parse input data
    if args.input in 'irdb':
        import csv
        import requests

        base = 'http://cdn.rawgit.com/probonopd/irdb/master/codes'
        with requests.Session() as s:
            download = s.get('{}/{}'.format(base, args.path))
            content = download.content.decode('utf-8')
            for row in csv.DictReader(content.splitlines(), delimiter=','):
                code = {'functionname': row['functionname'],
                        'raw': irgen.gen_raw_general(**row)}
                codes.append(code)

    elif args.input == 'raw':
        code = {
            'functionname': 'raw',
            'raw': [float(x) for x in args.data]
        }
        codes.append(code)
    elif args.input == 'broadlink_base64':
        code = {
            'functionname': 'base64',
            'raw': irgen.gen_raw_from_broadlink_base64(args.data[0].encode())
        }
        codes.append(code)
    elif args.input == 'pronto':
        code = {
            'functionname': 'pronto',
            'raw': irgen.gen_raw_from_pronto(int(x, base=16) for x in args.data)
        }
        codes.append(code)
    else:
        code = {
            'functionname': '{}({})'.format(args.input,
                                            ','.join(map(str, args.data))),
            'raw': raw.paired(
                raw.simplify(
                irgen.gen_raw_general(args.input, *args.data)))
        }
        codes.append(code)

    # Process raw data
    if args.repeats > 1:
        for code in codes:
            code['raw'] = list(code['raw'])*(args.repeats)

    # Generate output data
    if args.output == 'broadlink':
        for r in codes:
            v = bytes(irgen.gen_broadlink_from_raw(code['raw']))
            print(v.hex())

    elif args.output == 'broadlink_base64':
        for r in codes:
            v = bytes(irgen.gen_broadlink_base64_from_raw(code['raw']))
            print(v.decode('ascii'))

    elif args.output == 'raw':
        def signed(x):
            for v in x:
                if v > 0:
                    yield "+{}".format(v)
                else:
                    yield "{}".format(v)
        for code in codes:
            print(" ".join(signed(code['raw'])))

    elif args.output == "pronto":
        for code in codes:
            print(" ".join(irgen.gen_pronto_from_raw([], code['raw'], base=0x73)))

    elif args.output in irgen.dec_raw_protocols:
        parser = irgen.dec_raw_protocols[args.output]
        for code in codes:
            d = iter(list(code['raw']))
            while True:
                try:
                    print(parser(d))
                except StopIteration:
                    break

if __name__ == "__main__":
    main()