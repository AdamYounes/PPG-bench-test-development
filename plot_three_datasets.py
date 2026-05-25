"""
This script loads three PPG measurement files, extracts the PPG0 and AMBIENT channels, 
and plots them together for comparison. The PPG0 curves from the three measurements are plotted as solid lines, while the AMBIENT curves are plotted as dashed lines. 
The script also trims the data to the shortest length among the three files to ensure they are aligned on the time axis.
"""
import pandas as pd
import matplotlib.pyplot as plt

# === 1. Load time + PPG0 + AMBIENT from each file ===
def load_ppg0_ambient(file_path):
    df = pd.read_csv(file_path, delim_whitespace=True)
    df["time_s"] = (df["TIMESTAMP"] - df["TIMESTAMP"].iloc[0]) / 1e9
    # Return both PPG0 and AMBIENT (no averaging for AMBIENT)
    return df[["time_s", "PPG0", "AMBIENT"]]

# === 2. Load three files ===
df1 = load_ppg0_ambient("")
df2 = load_ppg0_ambient("")
df3 = load_ppg0_ambient("")

# === 3. Trim to common length (if different lengths) ===
min_len = min(len(df1), len(df2), len(df3))
df1 = df1.iloc[:min_len]
df2 = df2.iloc[:min_len]
df3 = df3.iloc[:min_len]

# === 4. Create average curve for PPG0 (not for AMBIENT) ===
avg_ppg0 = (df1["PPG0"] + df2["PPG0"] + df3["PPG0"]) / 3

# === 5. Plot ===
plt.figure(figsize=(14, 6))

# PPG0 (all three)
plt.plot(df1["time_s"], df1["PPG0"], label="Set 1 - PPG0")
plt.plot(df2["time_s"], df2["PPG0"], label="Set 2 - PPG0")
plt.plot(df3["time_s"], df3["PPG0"], label="Set 3 - PPG0")

# AMBIENT (all three; plotted separately, no averaging)
plt.plot(df1["time_s"], df1["AMBIENT"], label="Ambient light - Set 1", alpha=0.7)
plt.plot(df2["time_s"], df2["AMBIENT"], label="Ambient light - Set 2", alpha=0.7)
plt.plot(df3["time_s"], df3["AMBIENT"], label="Ambient light - Set 3", alpha=0.7)

# === 6. Layout ===
plt.title("PPG0 from three measurements +  Ambient (all sets)")
plt.xlabel("Time (seconds)")
plt.ylabel("Sensor output(Raw units)")
plt.legend(ncol=2)
plt.grid(True)
plt.tight_layout()
plt.show()
