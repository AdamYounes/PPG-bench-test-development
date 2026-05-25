#!/usr/bin/env python3
"""PPG linearity & operating-zone characterisation (LED / LCD).

Each trial: an AFG sync pulse at the start (used only to time-align the two
logs, never plotted) followed by a voltage staircase. It handles both the LED rig (signal rises with V) and the
LCD rig (signal falls with V). Set SETUP and run.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress

# --- configuration ---------------------------------------------------------
SETUP = "LCD"

CONFIG = {
    "LED": dict(
        data_dir="PPGLED_response/", channel="PPG0", v_min=0.10, v_max=1.10,
        ylabel="Normalised emitted intensity",
        tests=[("PPG_LEDTEST_1.csv", "PPG_20260519_221133.txt"),
               ("PPG_LEDTEST_2.csv", "PPG_20260519_221238.txt"),
               ("PPG_LEDTEST_3.csv", "PPG_20260519_221322.txt")],
    ),
    "LCD": dict(
        data_dir="PPGLCD_response", channel="PPG0", v_min=0.10, v_max=4.90,
        ylabel="Normalised transmittance",
        tests=[("PPG_LCDTEST_1.csv", "PPG_20260517_1.txt"),
               ("PPG_LCDTEST_2.csv", "PPG_20260517_2.txt"),
               ("PPG_LCDTEST_3.csv", "PPG_20260517_3.txt")],
    ),
}

R2_MIN, MIN_SPAN, MIN_PTS = 0.99, 0.20, 4   # linearity criteria
SETTLE, TAIL = 0.30, 0.10                   # dwell-sampling window fractions


# --- per-trial processing ---------------------------------------------------
def process(csv_file, txt_file, cfg):
    """Return a tidy frame (V, S, T) for one trial, or None on failure."""
    csv_p = os.path.join(cfg["data_dir"], csv_file)
    txt_p = os.path.join(cfg["data_dir"], txt_file)
    if not (os.path.exists(csv_p) and os.path.exists(txt_p)):
        return None

    afg = pd.read_csv(csv_p, dtype={"Timestamp": "string"})
    ts = pd.to_datetime(afg["Timestamp"], format="%H:%M:%S.%f")
    afg["t"] = ts.dt.hour * 3600 + ts.dt.minute * 60 + ts.dt.second + ts.dt.microsecond / 1e6
    afg["V"] = pd.to_numeric(afg["Peak_Voltage_V"], errors="coerce").fillna(0.0)

    ppg = pd.read_table(txt_p, sep=r"\s+", comment="#", engine="python")
    ppg["t"] = ppg["TIMESTAMP"] / 1e9
    s = ppg[cfg["channel"]].to_numpy(float)

    # Start-anchored sync: align the AFG marker (row 0) with the first PPG
    # excursion past 30% of the signal range, works for rise or fall.
    base, rng = np.median(s[:5]), s.max() - s.min()
    if rng == 0:
        return None
    rise = np.argmax(np.abs(s - base) > 0.30 * rng)
    ppg["ta"] = ppg["t"] - (ppg["t"].iloc[rise] - afg["t"].iloc[0])

    # Staircase starts after the marker returns to ~0 V.
    end = np.argmax(afg["V"].to_numpy()[1:] <= cfg["v_min"]) + 1
    stair = afg.iloc[end:].reset_index(drop=True)
    nxt = stair["t"].shift(-1)
    nxt = nxt.fillna(stair["t"] + (nxt - stair["t"]).median())

    rows = []
    for v, t0, t1 in zip(stair["V"], stair["t"], nxt):
        if not (cfg["v_min"] <= v <= cfg["v_max"]) or (t1 - t0) < 0.2:
            continue
        seg = ppg[(ppg["ta"] >= t0 + SETTLE * (t1 - t0)) & (ppg["ta"] <= t1 - TAIL * (t1 - t0))]
        if not seg.empty:
            rows.append((v, seg[cfg["channel"]].mean()))
    if not rows:
        return None

    agg = pd.DataFrame(rows, columns=["V", "S"]).groupby("V", as_index=False).mean()
    lo, hi = agg["S"].min(), agg["S"].max()
    agg["T"] = (agg["S"] - lo) / (hi - lo) if hi != lo else 0.0
    return agg


def linear_window(agg):
    """Widest voltage window with R^2 >= R2_MIN; ties broken by R^2."""
    v, t, n = agg["V"].to_numpy(), agg["T"].to_numpy(), len(agg)
    best = (None, None, None, -1.0, -1.0)  # lo, hi, reg, span, r2
    for i in range(n - MIN_PTS + 1):
        for j in range(i + MIN_PTS - 1, n):
            if abs(t[j] - t[i]) < MIN_SPAN:
                continue
            reg = linregress(v[i:j + 1], t[i:j + 1])
            r2, span = reg.rvalue ** 2, abs(v[j] - v[i])
            if r2 >= R2_MIN and (span, r2) > (best[3], best[4]):
                best = (v[i], v[j], reg, span, r2)
    return best[:3]


# --- run + plot -------------------------------------------------------------
def main():
    cfg = CONFIG[SETUP]
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(14, 6))
    colors = plt.cm.tab10(np.linspace(0, 0.9, len(cfg["tests"])))
    zones, fits = [], []

    for (csv_file, txt_file), c in zip(cfg["tests"], colors):
        agg = process(csv_file, txt_file, cfg)
        if agg is None:
            print(f"[skip] {txt_file}")
            continue
        name = os.path.splitext(os.path.basename(txt_file))[0]
        axa.plot(agg["V"], agg["S"], "o-", color=c, ms=4, lw=1.5, label=name)

        lo, hi, reg = linear_window(agg)
        if reg is None:
            axb.plot(agg["V"], agg["T"], "o--", color=c, ms=4, lw=1, alpha=.5, label=name)
            continue
        lo, hi = sorted((lo, hi))
        zones.append((lo, hi)); fits.append((reg.slope, reg.intercept))
        axb.plot(agg["V"], agg["T"], "o-", color=c, ms=4, lw=1.5, alpha=.75,
                 label=f"{name} ({lo:.2f}-{hi:.2f} V)")

    if zones:
        vlo, vhi = np.mean([z[0] for z in zones]), np.mean([z[1] for z in zones])
        m, b = np.mean([f[0] for f in fits]), np.mean([f[1] for f in fits])
        xs = np.linspace(max(0, vlo - .2), min(5, vhi + .2), 50)
        axb.plot(xs, m * xs + b, color="crimson", lw=2.5, label="Avg linear system fit")
        axb.axvspan(vlo, vhi, alpha=.12, color="darkorange",
                    label=f"Linear zone (R²≥{R2_MIN}): {vlo:.2f}-{vhi:.2f} V")
        print(f"{SETUP}: linear zone {vlo:.2f}-{vhi:.2f} V, slope {m:.3f} units/V")

    axa.set(xlabel="AFG Peak Voltage (V)", ylabel="Raw sensor output", title="Graph A : Raw Sensor Output")
    axb.set(xlabel="AFG Peak Voltage (V)", ylabel=cfg["ylabel"],
            title=f"Graph B : Linear Operating Zone (R²≥{R2_MIN})", ylim=(-.05, 1.05))
    for ax in (axa, axb):
        ax.grid(True, ls=":", alpha=.6); ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(f"linearity_{SETUP}.png", dpi=200, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
