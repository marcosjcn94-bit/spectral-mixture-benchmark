import argparse
import csv
import hashlib
import json
import platform
import subprocess
from importlib.metadata import version
from itertools import groupby, product
from pathlib import Path
from time import perf_counter

import numpy as np

from .figure import plot
from .model import AXIS, FRACTIONS, NOISE, SEED, SEPARATIONS, fit, reference, spectra

CONDITION = ("separation_sigma", "fraction_true", "noise_sd")
METRICS = ("fraction_error_pp", "reconstruction_rmse")


def observations(repeats):
    rng = np.random.Generator(np.random.PCG64(SEED))
    for separation, fraction, noise in product(SEPARATIONS, FRACTIONS, NOISE):
        first, second = spectra(separation)
        distance = float(np.linalg.norm(first - second))
        clean = fraction * first + (1 - fraction) * second
        for replicate in range(1, (repeats if noise else 1) + 1):
            observed = clean + rng.normal(0, noise, AXIS.size) if noise else clean
            optimum = reference(first, second, observed)
            results = fit(first, second, observed)
            for method, result in results.items():
                estimate = float(result.x[0])
                finite = np.isfinite(estimate)
                discrepancy = abs(estimate - optimum) if finite else None
                error = abs(estimate - fraction) if finite else None
                accepted = (
                    result.success and finite and -1e-10 <= estimate <= 1 + 1e-10
                    and discrepancy <= 1e-5 and (noise > 0 or error <= 1e-6)
                )
                yield dict(
                    separation_sigma=separation, fraction_true=fraction, noise_sd=noise,
                    distance_l2=distance, replicate=replicate, method=method,
                    estimate=estimate if finite else None, reference=optimum,
                    solver_status=int(result.status), solver_success=bool(result.success),
                    solver_iterations=int(result.nit), solver_message=str(result.message),
                    state="ok" if accepted else "failed",
                    reference_error=discrepancy,
                    fraction_error_pp=100 * error if finite else None,
                    reconstruction_rmse=rmse(observed, first, second, estimate) if finite else None,
                    reference_rmse=rmse(observed, first, second, optimum),
                )


def rmse(observed, first, second, fraction):
    return float(np.sqrt(np.mean((observed - (fraction * first + (1 - fraction) * second))**2)))


def summarize(rows):
    for key, group in groupby(rows, key=lambda row: tuple(row[name] for name in CONDITION)):
        condition = list(group)
        methods = ("reference", "BVLS", "SLSQP")
        for method in methods:
            attempts = [row for row in condition if row["method"] == ("BVLS" if method == "reference" else method)]
            summary = dict(zip(CONDITION, key, strict=True))
            summary.update(method=method, distance_l2=attempts[0]["distance_l2"], attempts=len(attempts))
            if method == "reference":
                errors = [100 * abs(row["reference"] - row["fraction_true"]) for row in attempts]
                residuals = [row["reference_rmse"] for row in attempts]
                failures = 0
            else:
                accepted = [row for row in attempts if row["state"] == "ok"]
                errors = [row["fraction_error_pp"] for row in accepted]
                residuals = [row["reconstruction_rmse"] for row in accepted]
                failures = len(attempts) - len(accepted)
            summary["failures"] = failures
            for metric, values in zip(METRICS, (errors, residuals), strict=True):
                summary[f"{metric}_median"] = float(np.median(values)) if values else None
                summary[f"{metric}_p90"] = float(np.quantile(values, 0.9)) if values else None
            yield summary


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def revision(root):
    if not (root / ".git").exists():
        return None
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run(output, repeats=100):
    start = perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    rows = list(observations(repeats))
    summary = list(summarize(rows))
    write_csv(output / "observations.csv", rows)
    write_csv(output / "summary.csv", summary)
    plot(summary, output / "figure.png", repeats)
    root = Path(__file__).resolve().parents[1]
    inputs = [*sorted(Path(__file__).parent.glob("*.py")), root / "PROTOCOL.md", root / "uv.lock"]
    manifest = {
        "seed": SEED, "rng": "PCG64", "noisy_replicates": repeats,
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: version(name) for name in ("numpy", "scipy", "matplotlib")},
        "git_revision": revision(root),
        "source_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in inputs},
        "mixtures": len(rows) // 2,
        "fits": len(rows),
        "failures": sum(row["state"] != "ok" for row in rows),
        "elapsed_seconds": perf_counter() - start,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{manifest['mixtures']:,} mixtures, {manifest['fits']:,} fits, {manifest['failures']} failures.")
    return int(manifest["failures"] > 0)


def main():
    parser = argparse.ArgumentParser(description="Run the synthetic spectral mixture benchmark.")
    parser.add_argument("--output", type=Path, required=True, help="new directory for the results")
    args = parser.parse_args()
    try:
        return run(args.output)
    except FileExistsError:
        parser.error(f"output already exists: {args.output}")


if __name__ == "__main__":
    raise SystemExit(main())
