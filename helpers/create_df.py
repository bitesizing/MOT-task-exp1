""" File designed to take in data from all existing pps and generate a dataframe. """
# %%

import glob
import pickle
import pandas as pd
from psychopy.tools.filetools import fromFile

from helpers import write_file, json_compatibalise

# Manual variables
save_df = False
data_folder = 'data/final/'
db_folder = 'data/dfs/'
suffix = 'psydat'
start, end = -1, -1  # pp numbers; -1 for last entry; inclusive

# Automated variables
file_list = glob.glob(data_folder + "/*" + suffix)  # list of all .psydat files
full_range = range(0, len(file_list)+1)  # range of all files
start_idx, end_idx = full_range[start], full_range[end]

all_entries, all_info = [], []
for pp_n in range(start_idx, end_idx+1):
    with open(f'{data_folder}MOT1_pp{pp_n}.{suffix}', 'rb') as file:
        e = pickle.load(file)

    break
    entries = fromFile(f"{data_folder}MOT1_pp{pp_n}.psydat").entries
    for entry in entries:
        new_entry = {'pp_n': pp_n}
        new_entry.update(entry)
        all_entries.append(new_entry)

    extra_info = fromFile(f"{data_folder}MOT1_pp{pp_n}.psydat").extraInfo
    all_info.append(extra_info)

if save_df:
    filename = f'{db_folder}' + '{}_' + f'{start_idx}-{end_idx}.' + '{}'
    write_file(pd.DataFrame(all_entries), filename.format("df", "pkl"))
    write_file(json_compatibalise(all_info), filename.format("pp-data", "json"))
