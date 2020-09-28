import pytest
from irgen import raw


def test_paired():
    assert list(raw.paired(
        [-1.0])) == [0.0, -1.0]
    assert list(raw.paired(
        [0.0 -1.0])) == [0.0, -1.0]
    assert list(raw.paired(
        [0.0, -1.0, -1.0])) == [0.0, -1.0, 0.0, -1.0]
    assert list(raw.paired(
        [0.0, -1.0, -1.0, 1.0])) == [0.0, -1.0, 0.0, -1.0, 1.0, 0.0]


@pytest.mark.parametrize("input, output", [
    ([1, -1], [1, -1]),
    ([1, -1, 1], [1, -1, 1]),
    ([-2, 1, -1, 1], [1, -1, 1]),
])
def test_simplified(input, output):
    assert list(raw.simplify(input)) == output


@pytest.mark.parametrize("input, output", [
    ([1, -1], [1]),
    ([1, -1, 1], [1, -1, 1]),
])
def test_rtrim(input, output):
    assert list(raw.rtrim(input)) == output
