# DSP Toolkit (Task 2)

Python project with a Tkinter GUI for generating and displaying sine / cosine signals.

## Run
    pip install -r requirements.txt
    python app.py

On Linux, Tkinter may need: `sudo apt install python3-tk`

## Features
1. Display a signal in continuous (analog curve) or discrete (stem) representation
2. Menu **Signal Generation** -> **Sine wave** / **Cosine wave**: choose A, theta, analog frequency F
   and sampling frequency Fs (Fs must be > 2F, otherwise the sampling theorem error is shown)
3. Two signals at the same time: select both in the list, then "Plot selected"
   (tick "Overlay on one plot" to draw them on the same axes)

## Files
- `app.py` - GUI
- `dsp_core.py` - signal logic (reused by future tasks)
