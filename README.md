# MOT_task
A repository for my PsychoPy multiple object tracking experiment 1 code. 

# Installation
1) Clone repository using `https://github.com/bitesizing/mot-task-exp-1.git`.
2) Install stable release of [Python 3.10](https://www.python.org/downloads/release/python-3100/) for Windows 64-bit installer.
3) Create virtual environment if desired. Add `requirements.txt` as dependencies to install required packages (or install manually)

# Setup
- For non-blurry visuals on 2 and 4k monitors:
    - display scaling will need to be set to 100% in Windows, using `Settings -> System -> Display -> Scale and Layout`.
    - You will also need to go into advanced scaling settings (on the same page), and disable `Fix scaling for apps`.
- All experimental parameters can be modified in `constants.py`.
    - For information about specific parameters, check docstrings in `helpers/setting_dataclasses.py`.
    - `use_eyetracker` should be set to False as currently this only works for Tobii Fusion Pro. When False, this will use mouse position. 

# Running
- Simply run script `main.py` to begin the experiment. By default, data will be saved to `data/final`. 