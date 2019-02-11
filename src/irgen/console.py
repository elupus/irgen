import irgen


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
                        choices=[*irgen.gen_raw_nec_protocols,
                                 'raw',
                                 'irdb',
                                 'broadlink'
                                 'broadlink_base64'])
    parser.add_argument('-o', dest='output', type=str,
                        required=True,
                        help='Output protocol',
                        choices=['broadlink',
                                 'broadlink_hass',
                                 'broadlink_base64',
                                 'raw'])

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
            'raw': args.data
        }
        codes.append(code)
    elif args.input == 'broadlink_base64':
        code = {
            'functionname': 'base64',
            'raw': irgen.gen_raw_from_broadlink_base64(args.data[0].encode())
        }
        codes.append(code)
    else:
        code = {
            'functionname': '{}({})'.format(args.input,
                                            ','.join(map(str, args.data))),
            'raw': irgen.gen_raw_general(args.input, *args.data)
        }
        codes.append(code)

    # Generate output data
    if args.output == 'broadlink':
        for r in codes:
            v = bytes(irgen.gen_broadlink_from_raw(code['raw']))
            print(v.hex())

    elif args.output == 'broadlink_base64':
        for r in codes:
            v = b64encode(bytes(
                irgen.gen_broadlink_from_raw(code['raw']))).decode()
            print(v)

    elif args.output == 'broadlink_hass':
        from base64 import b64encode
        from collections import OrderedDict
        from yaml import dump, safe_dump

        group = dict()
        group['entities'] = []
        for code in codes:
            group['entities'].append(gen_hass_entityname(code['functionname']))

        switch = dict()
        switch['switches'] = dict()
        for code in codes:
            v = bytes(irgen.gen_broadlink_from_raw(code['raw']))
            entity = dict()
            entity['command_on'] = b64encode(v).decode()
            entity['friendlyname'] = code['functionname']
            switch['switches'][irgen.gen_hass_entityname(
                code['functionname'])] = entity
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
