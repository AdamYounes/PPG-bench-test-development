"""
Script used for calculating the AC peak to peak values, alongside the DC offset and AC/DC ratio.
Script was co-created with github copilot.
"""
import pandas as pd
import numpy as np
from scipy import signal
 
FILES = ['PPG_20260517_210819_LCD.txt', 'PPG_20260521_143545_LED.txt',
         'PPG_20260429_172421_wrist.txt']
 
for f in FILES:
    df = pd.read_csv(f, sep=r'\s+')
    fs = 1e9 / np.median(np.diff(df['TIMESTAMP']))
    sig = df['PPG0'].values.astype(float)
    sos = signal.butter(4, [0.7, 4], btype='band', fs=fs, output='sos')
    ac = signal.sosfiltfilt(sos, sig)
    ac_pp = np.percentile(ac, 95) - np.percentile(ac, 5)
    print(f"{f}: DC={sig.mean():.0f}  AC_pp={ac_pp:.0f}  AC/DC={ac_pp/sig.mean()*100:.2f}%")
