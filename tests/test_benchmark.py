import csv

import numpy as np
import pytest

from spectral_benchmark.model import fit, reference, spectra
from spectral_benchmark.__main__ import run


@pytest.mark.parametrize("p", [0, 0.1, 0.5, 0.9, 1])
@pytest.mark.parametrize("separation", [0.25, 4])
def test_noiseless(p, separation):
    first, second = spectra(separation)
    observation = p * first + (1 - p) * second
    expected = reference(first, second, observation)
    assert expected == pytest.approx(p, abs=1e-14)
    for result in fit(first, second, observation).values():
        assert result.success
        assert result.x[0] == pytest.approx(p, abs=1e-6)


@pytest.mark.parametrize(("unbounded", "expected"), [(-0.2, 0), (1.3, 1)])
def test_optimum_at_bound(unbounded, expected):
    first, second = spectra(1)
    observation = second + unbounded * (first - second)
    assert reference(first, second, observation) == expected
    for result in fit(first, second, observation).values():
        assert result.success
        assert result.x[0] == pytest.approx(expected, abs=1e-10)


def test_identical_spectra():
    signal = np.ones(9)
    assert reference(signal, signal, signal) is None
    assert fit(signal, signal, signal) == {}


def test_pipeline_smoke(tmp_path):
    output = tmp_path / "run"
    assert run(output, repeats=1) == 0
    with (output / "observations.csv").open(newline="") as table:
        rows = list(csv.DictReader(table))
    assert len(rows) == 200
    assert {row["state"] for row in rows} == {"ok"}
    assert (output / "figure.png").stat().st_size > 0
    with pytest.raises(FileExistsError):
        run(output, repeats=1)
