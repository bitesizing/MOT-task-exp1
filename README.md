# MOT_task
A repository for my PsychoPy multiple object tracking experiment 1 code. 

# Installation guidelines
1) Clone repository using `https://github.com/bitesizing/MOT_task.git`.
2) Install stable release of [Python 3.10](https://www.python.org/downloads/release/python-3100/) for Windows 64-bit installer.
3) Create virtual environment if desired. Add `requirements.txt` as dependencies to install required packages. (will not work if `requirements.txt` is hidden). Alternatively, install dependencies manually.


# Running requirements
- For non-blurry visuals on 2 and 4k monitors:
    - display scaling will need to be set to 100% in Windows, using `Settings -> System -> Display -> Scale and Layout`
    - You will also need to go into advanced scaling settings (on the same page), and disable `Fix scaling for apps`.
- All experimental parameters can be modified in `all_vars.py` and will (hopefully!) be clearly labelled. However, it is advised to:
    - Check `DisplayInfo()` in `all_vars.py` to see default monitor settings (screen size, framerate, etc.). If your device has non-default settings, you can add them to `utils -> device_presets.py` under your device name to override defaults automatically on a specific device. To find your device name, simply run `os.environ['COMPUTERNAME']` in a terminal.
    - You will also need to set `use_eyetracker = False` in `TestingParameters()` - currently this setting only works for Tobii Fusion Pro. When this is set to False, it will use mouse position. 
- Then, simply run `__run_task.py` and the experiment will begin!