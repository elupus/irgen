from sqlalchemy.sql.expression import func
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

def test_broadlink_decode_encode():
    data = b"JgAcAB0dOjo6HR0dHR0dHR0dHR0dHR0dHTodAAtnDQUAAAAAAAAAAAAAAAA="
    raw  = list(irgen.gen_raw_from_broadlink_base64(data))
    data2 = bytes(irgen.gen_broadlink_base64_from_raw(raw))
    assert data == data2

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


@pytest.mark.parametrize("device, function, toggle", [
    (2, 4, 0),
    (5, 66, 0)
])
def test_rc5_round_about(device, function, toggle):
    data = irgen.gen_raw_rc5(device, function, toggle)
    assert irgen.dec_raw_rc5(data) == (device, function, toggle)


@pytest.mark.parametrize("device, function, toggle, mode", [
    (2, 4, 0, 0),
    (5, 66, 0, 0)
])
def test_rc6_round_about(device, function, toggle, mode):
    data = irgen.gen_raw_rc6(device, function, toggle, mode)
    assert irgen.dec_raw_rc6(data) == (device, function, toggle, mode)