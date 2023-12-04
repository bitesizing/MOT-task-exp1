# MOT_task
A repository for my PsychoPy multiple object tracking experiment 1 code. 

# Installation guidelines
1) Clone repository using `https://github.com/bitesizing/MOT_task.git`.
2) Install stable release of [Python 3.10](https://www.python.org/downloads/release/python-3100/) for Windows 64-bit installer.
3) Create virtual environment. Add `requirements.txt` as dependencies (NOTE: this will not work if `requirements.txt` is hidden).
4) Once `.venv` is created, you can now hide it and `requirements.txt` with no issues (e.g. using `Make Hidden` extension).

# Running requirements
- For best visuals on 2 and 4k monitors, display scaling will need to be set to 100% in Windows, using `Settings -> System -> Display -> Scale and Layout`
    - You will also need to go into advanced scaling settings (on the same page), and disable 'Fix scaling for apps' setting.
- Make sure to go into `utils -> device_presets.py` and add your device display settings. Check `DisplayInfo()` for default vars.
- You will also need to set `use_eyetracker = False` in `TestingParameters()`, as this currently only works with one specific eyetracker model.