import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from .model import NOISE, SEPARATIONS


def plot(summary, output, repeats):
    fig, axes = plt.subplots(1, 2, sharex=True, figsize=(8.2, 3.5), layout="constrained")
    metrics = ("fraction_error_pp_median", "reconstruction_rmse_median")
    labels = ("Absolute fraction error (pp)", "Reconstruction RMSE")
    colors = ("#444444", "#0072B2", "#008461", "#BA4300")
    markers = ("x", "o", "s", "^")
    for noise, color, marker in zip(NOISE, colors, markers, strict=True):
        rows = [row for row in summary if row["method"] == "reference"
                and row["fraction_true"] == 0.5 and row["noise_sd"] == noise]
        for ax, metric in zip(axes, metrics, strict=True):
            ax.plot(SEPARATIONS, [row[metric] for row in rows], color=color, marker=marker,
                    linewidth=1.4, markersize=4.5, label=f"{noise:.2f}")
    for ax, label, title in zip(axes, labels, ("A  Composition", "B  Reconstruction"), strict=True):
        ax.set_xscale("log", base=2)
        ax.set_xticks(SEPARATIONS, [str(value) for value in SEPARATIONS])
        ax.minorticks_off()
        ax.set(xlabel="Peak separation (Gaussian widths)", ylabel=label, ylim=(0, None))
        ax.set_title(title, loc="left", fontweight="medium")
        ax.grid(axis="y", color="#dddddd", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(title="Noise SD", frameon=False)
    fig.suptitle(f"50/50 mixtures · analytic optimum · medians of {repeats} noisy replicates", fontsize=11)
    fig.savefig(output, dpi=220, facecolor="white")
    plt.close(fig)
