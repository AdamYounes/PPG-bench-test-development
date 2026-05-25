import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# === 1. Läs in rådata utan normalisering ===
def load_raw(file_path):
    df = pd.read_csv(file_path, sep=r'\s+', engine='python')
    df["time_s"] = (df["TIMESTAMP"] - df["TIMESTAMP"].iloc[0]) / 1e9
    return df

# === 2. Läs in två filer ===
#df1 = load_raw("PPG_20250729_220815_fingertest1.txt")
#df1 = load_raw("PPG_20250804_013435_ambient_with_diode.txt")
df1 = load_raw("HRvsPPG_data/Polar raw data LED/Steady 60/PPG_20260522_180331.txt")
df2 = load_raw("HRvsPPG_data/Polar raw data LED/Steady 210/PPG_20260522_184829.txt")
#df2 = load_raw("PPG_20250729_215152_2.1OFF_300mVp.txt")

# === 3. Align data by time for averaging ===
# Find overlapping time range
time_min = max(df1["time_s"].min(), df2["time_s"].min())
time_max = min(df1["time_s"].max(), df2["time_s"].max())

# Create common time grid (1000 points for smoothness)
common_time = np.linspace(time_min, time_max, 1000)

# Interpolate PPG0 for both datasets
df1_ppg0_interp = np.interp(common_time, df1["time_s"], df1["PPG0"])
df2_ppg0_interp = np.interp(common_time, df2["time_s"], df2["PPG0"])

# Compute average
avg_ppg0 = (df1_ppg0_interp + df2_ppg0_interp) / 2

# === 4. Plot – råa signaler ===
plt.figure(figsize=(14, 6))

# Dataset 1
plt.subplot(2, 1, 1)
plt.plot(df1["time_s"], df1["PPG0"], label="Set 1 - PPG0")

plt.plot(df1["time_s"], df1["AMBIENT"], linestyle="--")
plt.title("Raw PPG data from LED at 60 bpm")
plt.xlabel("Time (seconds)")
plt.ylabel("Signal Output (raw units)")
plt.legend(ncol=2)
plt.grid(True)
plt.tight_layout()
# Dataset 2
plt.subplot(2, 1, 2)
plt.plot(df2["time_s"], df2["PPG0"], label="Set 2 - PPG0")

plt.plot(df2["time_s"], df2["AMBIENT"], linestyle="--")

#plt.plot(common_time, avg_ppg0, label="Average PPG0", linewidth=1.5, linestyle="--")

# === 5. Layout ===
plt.title("Raw PPG data from LED at 210 bpm")
plt.xlabel("Time (seconds)")
plt.ylabel("Signal Output (raw units)")
plt.legend(ncol=2)
plt.grid(True)
plt.tight_layout()
plt.show()
