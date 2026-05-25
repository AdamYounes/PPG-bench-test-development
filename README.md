# Development and Validation of a Controlled Bench-Test Setup for PPG-Based Heart-Rate Sensors

This repository contains the data and Python analysis scripts for my Bachelor's thesis in Medical Technology at KTH Royal Institute of Technology.

## Project Overview
The aim of this project was to develop and validate a controlled bench-test setup that acts as a repeatable Photoplethysmography (PPG) signal source for wrist-worn, heart rate monitors. 

Validating PPG sensors on human subjects introduces uncontrollable variables like motion artifacts and ambient light. To bypass this, the project introduces two complementary laboratory setups driven by a Tektronix AFG 1022 Arbitrary Function Generator:
* **Light Emitting Setup:** Generates a synthesized PPG signal through an LED, utilizing a MOSFET to gate the LED so it only turns on in sync with the device's own sampling window.
* **Light Modulating Setup:** Attenuates the device's own emitted light via a twisted-nematic (TN) liquid-crystal shutter.

Both setups were validated against commercial devices (Polar Verity Sense, Apple Watch Series 9, Garmin Forerunner 255, and Wahoo TICKR Fit) across an exercise range of 60 to 210 bpm.

## Installation & Setup

If you intend to run the hardware communication script (`afg_connection.py`) to control the Tektronix AFG, you must configure your environment properly:

1. **Install NI-VISA:** You must install the NI-VISA backend from National Instruments for your operating system. The Python library relies on this backend to communicate over USB.
2. **Install Python Dependencies:** Install the required libraries using pip:
   ```bash
   pip install pyvisa pandas numpy matplotlib scipy tektronix_func_gen

## Repository Structure

* `afg_connection.py`: PyVISA script used to send commands and custom waveforms to the Tektronix AFG 1022, and to automate the linearity voltage sweeps.
* `plot_setup_response.py`: Characterizes the linear operating zones for both the LED emission and LCD attenuation setups.
* `plot_three_datasets.py`: Generates comparative plots of raw intensity data and ambient light readings across multiple datasets.
* `/compute_acdc`: Contains the `compute_acdc.py` script and the `/Wrist_data` folder used to isolate the cardiac component and calculate the peak-to-peak pulse amplitude (ACpp).
* `/PPGLCD_response`: Contains the data logs from the LCD shutter attenuation tests.
* `/PPGLED_response`: Data logs from the active LED setup linearity tests.
* `/HRvsPPG_data`: Contains the heart rate logs and raw PPG output folders captured during steady-state validation at 60, 90, 120, 180, and 210 bpm.
* `/3D CAD files`: Contains the Autodesk Fusion 360 schematics and STL files for 3D printing the test enclosures used in both setups.

## Author
Adam Younes 
Degree project in Medical Technology (First cycle, 15 credits)
KTH Royal Institute of Technology
