"""
Configured for Tektronix AFG 1022
Scripts used for performing response tests by sending commands to the AFG through PyVisa.
Run ppg_wave_setup to set custom waveform to the desired memory slot.
Requires PyVisa library to be downloaded, as well as install NI-VISA backend to configure usb port.
"""

import asyncio
from datetime import datetime, timedelta
import os
from pathlib import Path
import sys
import time
from tektronix_func_gen import FuncGen
import tektronix_func_gen as tfg
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv
import pyvisa

def set_custom_waveform(
    self,
    waveform: np.ndarray,
    normalise: bool = True,
    memory_num: int = 0,
    verify: bool = True,
    print_progress: bool = True,
):
    """Transfer waveform data to edit memory and then user memory.
    NOTE: Will overwrite without warnings

    Parameters
    ----------
    waveform : ndarray
        Either unnormalised arbitrary waveform (then use `normalise=True`),
        or ints spanning the resolution of the function generator
    normalise : bool
        Choose whether to normalise the waveform to ints over the
        resolution span of the function generator
    memory_num : str or int {0,...,255}, default 0
        Select which user memory to copy to
    verify : bool, default `True`
        Verify that the waveform has been transferred and is what was sent
    print_progress : bool, default `True`

    Returns
    -------
    waveform : ndarray
        The normalised waveform transferred

    Raises
    ------
    ValueError
        If the waveform is not within the permitted length or value range
    RuntimeError
        If the waveform transferred to the instrument is of a different
        length than the waveform supplied
    """
    if not 0 <= memory_num <= self._max_waveform_memory_user_locations:
        raise ValueError(
            f"The memory location {memory_num} is not a valid "
            "memory location for this model"
        )
    # Check if waveform data is suitable
    if print_progress:
        print("Check if waveform data is suitable..", end=" ")
    self._check_arb_waveform_length(waveform)
    try:
        self._check_arb_waveform_type_and_range(waveform)
    except ValueError as err:
        if print_progress:
            print(f"\n  {err}")
            print("Trying again normalising the waveform..", end=" ")
        waveform = self._normalise_to_waveform(waveform)
    if print_progress:
        print("ok")
        print("Transfer waveform to function generator..", end=" ")
    # Transfer waveform
    self._inst.write_binary_values(
        "DATA:DATA EMEMory,", waveform, datatype="H", is_big_endian=True
    )
    # Check for errors and check lengths are matching
    transfer_error = self.get_error()
    emem_wf_length = self.query("DATA:POINts? EMEMory")
    if emem_wf_length == "" or not int(emem_wf_length) == len(waveform):
        msg = (
            f"Waveform in temporary EMEMory has a length of {emem_wf_length}"
            f", not of the same length as the waveform ({len(waveform)})."
            f"\nError from the instrument: {transfer_error}"
        )
        raise RuntimeError(msg)
    if print_progress:
        print("ok")
        print(f"Copy waveform to USER{memory_num}..", end=" ")
    self.write(f"DATA:COPY USER{memory_num},EMEMory")
    if print_progress:
        print("ok")
    if verify:
        if print_progress:
            print(f"Verify waveform USER{memory_num}..")
        if f"USER{memory_num}" in self.get_waveform_catalogue():
            verif = self._verify_waveform(
                waveform,
                memory_num,
                normalise=normalise,
                print_result=print_progress,
            )
            if not verif[0]:
                raise RuntimeError(
                    f"USER{memory_num} does not contain the waveform"
                )
        else:
            raise RuntimeError(f"USER{memory_num} is empty")
    return waveform


def ppg_wave_setup(visa_address):
    import math
    pi = math.pi
    # Generate a time array
    time = np.linspace(1.07, 1.72, 1000)
    # Calculate the waveform
    data = 500 * np.cos(2 * pi * 1.5 * time) - 250 * np.sin(4 * pi * 1.5 * time) * -1 # Multiply by negative 1 to inverse it. Remove "*-1" for LCD.
 

    with tfg.FuncGen(visa_address) as fgen:
        fgen.set_custom_waveform(waveform = data, memory_num=1, verify=True)



def control(fgen: FuncGen, freq):
    fgen.ch1.set_frequency(freq, unit="Hz")


def set_initial_settings(fgen: FuncGen, freq):
    fgen.ch1.set_function("USER0")
    fgen.ch1.set_frequency(freq, unit="Hz")
    fgen.ch1.set_offset(3, unit="V")
    fgen.ch1.set_amplitude(4)
    fgen.ch1.set_output("ON")
    fgen.ch1.print_settings()

def run_LED_linearity_test(inst):
    # Test parameters
    START_V_PEAK = 0.0
    END_V_PEAK = 1.0    
    STEP_V_PEAK = 0.1      
    INTERVAL = 1.0      
    SYNC_DURATION = 2 
    try:
        inst.write('OUTPUT1:IMPEDANCE INF') 
        results = []

        # --- PULSE 1: START SYNC (5V Peak / 10Vpp) ---
        print(f"Pulse: START (2.2V Peak for {SYNC_DURATION}s)")
        inst.write('SOURCE1:FUNCTION:SHAPE DC')
        inst.write(f'SOURCE1:VOLTAGE:LEVEL:IMMEDIATE:OFFSET {END_V_PEAK}V')
        inst.write('OUTPUT1:STATE ON')
        results.append([datetime.now().strftime('%H:%M:%S.%f'), {END_V_PEAK}])
        time.sleep(SYNC_DURATION)

        # --- LINEARITY SWEEP (0V to 5V Peak) ---
        print(f"Sweep: BEGINNING at {START_V_PEAK}...")
        current_peak = START_V_PEAK
        while current_peak <= (END_V_PEAK + 0.01):

            inst.write('SOURCE1:FUNCTION:SHAPE DC')
            inst.write(f'SOURCE1:VOLTAGE:LEVEL:IMMEDIATE:OFFSET {current_peak}V')

            ts = datetime.now().strftime('%H:%M:%S.%f')
            results.append([ts, round(current_peak, 2)])
            
            print(f"[{ts}] Peak: {current_peak:.2f}V")
            time.sleep(INTERVAL)
            current_peak += STEP_V_PEAK

        # --- PULSE 2: END SYNC / DISCHARGE (True 0V DC) ---
        # We switch to DC function to force exactly 0V across terminals
        print(f"Pulse: END / DISCHARGE (0V DC for {SYNC_DURATION}s)")
        inst.write('SOURCE1:FUNCTION:SHAPE DC') # Switch to DC mode
        inst.write('SOURCE1:VOLTAGE:LEVEL:IMMEDIATE:OFFSET 0V') # Force 0V
        
        ts_end = datetime.now().strftime('%H:%M:%S.%f')
        results.append([ts_end, 0.0])
        time.sleep(SYNC_DURATION)

        # 4. Cleanup
        inst.write('OUTPUT1:STATE OFF')
        print("Test Complete. Output OFF.")

        # Save Log
        filename = "PPG_LEDTEST_9.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Peak_Voltage_V'])
            writer.writerows(results)
        print(f"Log saved to {filename}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'inst' in locals():
            inst.close()

def run_LCD_linearity_test(inst):
    # Test parameters
    START_V_PEAK = 0.0
    END_V_PEAK = 5.0    
    STEP_V_PEAK = 0.1      
    INTERVAL = 1.0      
    SYNC_DURATION = 2.0 
    FREQ = "60Hz"
    try:
        inst.write('OUTPUT1:IMPEDANCE INF') 
        results = []

        # --- PULSE 1: START SYNC (5V Peak / 10Vpp) ---
        print(f"Pulse: START (5V Peak for {SYNC_DURATION}s)")
        inst.write('SOURCE1:FUNCTION:SHAPE SQUARE')
        inst.write(f'SOURCE1:FREQUENCY:FIXED {FREQ}')
        inst.write('SOURCE1:VOLTAGE:LEVEL:IMMEDIATE:OFFSET 0V')
        inst.write('SOURCE1:VOLTAGE:AMPLITUDE 10.0VPP')
        inst.write('OUTPUT1:STATE ON')
        results.append([datetime.now().strftime('%H:%M:%S.%f'), 5.0])
        time.sleep(SYNC_DURATION)

        # --- LINEARITY SWEEP (0V to 5V Peak) ---
        print(f"Sweep: BEGINNING at {FREQ}...")
        current_peak = START_V_PEAK
        while current_peak <= (END_V_PEAK + 0.01):
            v_pp = current_peak * 2
            if v_pp < 0.001:
                inst.write('SOURCE1:FUNCTION:SHAPE DC')
                inst.write('SOURCE1:VOLTAGE:LEVEL:IMMEDIATE:OFFSET 0V')
            else:
                inst.write('SOURCE1:FUNCTION:SHAPE SQUARE')
                inst.write(f'SOURCE1:VOLTAGE:AMPLITUDE {v_pp}VPP')
            
            ts = datetime.now().strftime('%H:%M:%S.%f')
            results.append([ts, round(current_peak, 2)])
            
            print(f"[{ts}] Peak: {current_peak:.2f}V")
            time.sleep(INTERVAL)
            current_peak += STEP_V_PEAK

        # --- PULSE 2: END SYNC / DISCHARGE (True 0V DC) ---
        # We switch to DC function to force exactly 0V across terminals
        print(f"Pulse: END / DISCHARGE (0V DC for {SYNC_DURATION}s)")
        inst.write('SOURCE1:FUNCTION:SHAPE DC') # Switch to DC mode
        inst.write('SOURCE1:VOLTAGE:LEVEL:IMMEDIATE:OFFSET 0V') # Force 0V
        
        ts_end = datetime.now().strftime('%H:%M:%S.%f')
        results.append([ts_end, 0.0])
        time.sleep(SYNC_DURATION)

        # 4. Cleanup
        inst.write('OUTPUT1:STATE OFF')
        print("Test Complete. Output OFF.")

        # Save Log
        filename = "PPG_OPTEST_3.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Peak_Voltage_V'])
            writer.writerows(results)
        print(f"Log saved to {filename}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'inst' in locals():
            inst.close()



# --- EXECUTION ---
rm = pyvisa.ResourceManager()
VISA_ADDRESS = 'USB::0x0699::0x0353::2217045::INSTR' # Change depending on your own AFG Visa address
afg = rm.open_resource(VISA_ADDRESS)


if __name__ == "__main__":
    run_LCD_linearity_test(afg)
#    run_LED_linearity_test(afg)
#    ppg_wave_setup(visa_address)


