import irgen

def test_gen_paired_from_raw():
    assert list(irgen.gen_paired_from_raw(
        [-1.0])) == [0.0, -1.0]
    assert list(irgen.gen_paired_from_raw(
        [0.0 -1.0])) == [0.0, -1.0]
    assert list(irgen.gen_paired_from_raw(
        [0.0, -1.0, -1.0])) == [0.0, -1.0, 0.0, -1.0]
    assert list(irgen.gen_paired_from_raw(
        [0.0, -1.0, -1.0, 1.0])) == [0.0, -1.0, 0.0, -1.0, 1.0, 0.0]