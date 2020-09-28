from base64 import b64decode
import irgen
import pytest

def test_gen_paired_from_raw():
    assert list(irgen.gen_paired_from_raw(
        [-1.0])) == [0.0, -1.0]
    assert list(irgen.gen_paired_from_raw(
        [0.0 -1.0])) == [0.0, -1.0]
    assert list(irgen.gen_paired_from_raw(
        [0.0, -1.0, -1.0])) == [0.0, -1.0, 0.0, -1.0]
    assert list(irgen.gen_paired_from_raw(
        [0.0, -1.0, -1.0, 1.0])) == [0.0, -1.0, 0.0, -1.0, 1.0, 0.0]


@pytest.mark.parametrize("data", [
    b"JgDgAAABKpEVERQRFREUERURFBEVERQRFTUVNhQ2FTYUNhU1FTYUNhURFBEVERQ2FTYUERURFBEVNRU2FDYVERQRFTUVNhQ2FQAFJAABKkkUAAxqAAEqRhcADGoAASpJFAAMagABK0gVAAxqAAEqSRQADGsAASpIFQAMagABKkcWAAxqAAEqSRQADGoAASpJFAAMagABK0YXAAxqAAEqSRQADGoAAStIFQAMagABK0gVAAxpAAErSBUADGoAASpIFQAMagABKkkUAAxrAAEqSRQADGoAAStIFQAMagABK0gVAA0FAAAAAAAAAAA=",
    b"JgA6AJdPJhwPHCYcJxw+HAACGxwOHA8cDhwPHA8bDxwPGwAHIxw+HFYcJxw+HCYcPxs/HCYcJwAChJ4ADQUAAAAAAAAAAAAAAAAAAA==",
    b"JgBYAFYhDh4MEBANDCEaEA8ODw4PDg8ODw4PDg8ODw4PDg4PDg8eDg0eDBEOAArPViEMHwwRDg8NIBoQDg8ODw4PDg8ODw4PDg8PDg8ODg8PDh4NDh8ODgwADQU=",
    b"JgBYAAABKJURFBITEjgVERMSFBESExIUEjgSOBQREzcSOBI4EzcWNRITEhMWDxM3FRESExITEhMSOBI4EjkSExI4ETkRORI4EwAFEAABKEsTAAxPAAEoSxMADQU=",
    b"JgAaAB0dOh0dHR0dHR0dHR0dHR0dOh0dOh0dAA0FAAAAAAAAAAAAAAAAAAA=",
])
def test_broadlink_decode_encode(data):
    raw  = list(irgen.gen_raw_from_broadlink_base64(data))
    data2 = bytes(irgen.gen_broadlink_base64_from_raw(raw))
    assert  b64decode(data2).hex() == b64decode(data).hex()



def test_rca38_decode_encode():
    """
    data was generated with IrScrutinizer-2.2.6 device 12, OBC 123
    """
    data = [+3680,-3680,+460,-1840,+460,-1840,+460,-920,+460,-920,+460,-920,+460,-1840,+460,-1840,+460,-1840,+460,-1840,+460,-920,+460,-1840,+460,-1840,+460,-920,+460,-920,+460,-1840,+460,-1840,+460,-1840,+460,-920,+460,-920,+460,-920,+460,-920,+460,-1840,+460,-920,+460,-920,+460,-7360]
    assert data == list(irgen.gen_raw_general('rca38', 12, -1, 123))


def test_gen_bitified_from_raw():
    assert list(irgen.gen_bitified_from_raw([100, 200], 100)) == [1, 1, 1]
    assert list(irgen.gen_bitified_from_raw([100, -200], 100)) == [1, -1, -1]

    with pytest.raises(Exception):
        list(irgen.gen_bitified_from_raw([100, -200*0.85], 100))

    with pytest.raises(Exception):
        list(irgen.gen_bitified_from_raw([100, -200*1.15], 100))


@pytest.mark.parametrize("device, function", [
    (2, 4),
    (5, 66)
])
def test_rc5_round_about(device, function):
    data = []
    data.extend(irgen.gen_raw_rc5(device, function, 0))
    data.extend(irgen.gen_raw_rc5(device, function, 1))
    x = iter(data)
    assert irgen.dec_raw_rc5(x) == (device, function, 0)
    assert irgen.dec_raw_rc5(x) == (device, function, 1)


@pytest.mark.parametrize("device, function, mode", [
    (2, 4, 0),
    (5, 66, 0)
])
def test_rc6_round_about(device, function, mode):
    data = []
    data.extend(irgen.gen_raw_rc6(device, function, 0, mode))
    data.extend(irgen.gen_raw_rc6(device, function, 1, mode))
    x = iter(data)
    assert irgen.dec_raw_rc6(x) == (device, function, 0, mode)
    assert irgen.dec_raw_rc6(x) == (device, function, 1, mode)


@pytest.mark.parametrize("input, output", [
    ([1, -1], [1, -1]),
    ([1, -1, 1], [1, -1, 1]),
    ([-2, 1, -1, 1], [1, -1, 1]),
])
def test_simplified(input, output):
    assert list(irgen.gen_simplified_from_raw(input)) == output


@pytest.mark.parametrize("input, output", [
    ([1, -1], [1]),
    ([1, -1, 1], [1, -1, 1]),
])
def test_trim_trailer(input, output):
    assert list(irgen.gen_trimmed_trailer(input)) == output
