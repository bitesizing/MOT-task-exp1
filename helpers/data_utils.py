""" File for flatten() function, which returns all items in sub-lists and sub-dictionaries as 1-d struct for iteration purposes.
"""
import os
import csv
import yaml
import numpy as np
import pickle as pkl
import json
from dataclasses import asdict, is_dataclass
from typing import Union

def flatten(l):
    """ Iterates through d.values(), including through lists and sub-dictionaries. """
    if isinstance(l, dict): 
        for value in l.values():
            yield from flatten(value)
    elif isinstance(l, list):
        for value in l:
            yield from flatten(value)
    else:
        yield l

def recursive_unpack_class(instance: object) -> dict:
    """
    Unpacks all the instance AND class variables in a class. Gives priority to variable values in the instance (will overwrite class variables of the same name).
    
    Args:
        instance (object): The instance of the class to unpack.
    
    Returns:
        dict: A dictionary containing the unpacked variables.
    """
    def unpack_class(instance):
        unpacked = {}
        for key, value in {**instance.__class__.__dict__, **vars(instance)}.items():
            if  ((key.startswith('__')) or  # no private variables
                (callable(value)) or  # no methods
                (callable(getattr(value, "__get__", None)))): # no descriptors (e.g. get-set descriptors)
                continue
            unpacked[key] = handle(value)
        return unpacked
    
    def unpack_iterable(iterable):
        result = []
        for element in iterable:
            result.append(handle(element))
        return result
    
    def unpack_dict(dictionary):
        result = {}
        for key, value in dictionary.items():
            result[key] = handle(value)
        return result
    
    def handle(item):
        if hasattr(item, '__dict__'):
            return unpack_class(item)
        elif isinstance(item, (list, tuple)):
            return unpack_iterable(item)    
        elif isinstance(item, dict):
            return unpack_dict(item)
        else:
            return item

    return unpack_class(instance)

def dict_pack(data: Union[dict, list, tuple], first: bool = True) -> Union[dict, list]:
    """Converts a data structure into a dictionary. Input can be a dictionary, list, or dataclass.
    Args:
        data: The data structure to be converted.
        first: Boolean flag to indicate if it's the first recursion.
    Returns:
        The converted data structure as a dictionary.
        
    Raises:
        TypeError: If the input is not a dataclass, dict, list, or tuple.
    """
    # Handle dataclasses by returning asdict(). Doesn't need to be recursive bc asdict() already is.
    if is_dataclass(data):
        return asdict(data)
    
    # Handle dicts by recursing for each value in dict.
    elif isinstance(data, dict):
        data = {key: dict_pack(value, first=False) for key, value in data.items()}

    # Handle lists and tuples by recursing for each item.
    elif isinstance(data, (list, tuple)):
        data = [dict_pack(item, first=False) for item in data]

    # If first time, return error if input is not dataclass, dict or list
    else:
        if first == True: raise TypeError('Must be list, dict or dataclass!')
    
    # Return data once it has been processed
    return data

def dict_unpack(obj, data: dict, first=True) -> object:
    if is_dataclass(obj):
        obj.__dict__.update(data)
    elif isinstance(obj, dict):
        obj = {key: dict_unpack(obj[key], data[key], first=False) for key in obj.keys()}
    elif isinstance(obj, list):
        obj = [dict_unpack(obj_item, data_item) for obj_item, data_item in zip(obj, data)]
    else:
        if first == True: raise TypeError('Obj must be list, dict or dataclass!')
    return obj


def json_compatibalise(obj):
    """ Converts hierarchical format into a format that can be turned into a json file. """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: json_compatibalise(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [json_compatibalise(item) for item in obj]
    else:
        return obj
    
def write_file(data, filepath: str):
    file_format = filepath.split('.')[-1]
    legal_formats = ['json', 'csv', 'pkl', 'psydat', 'yaml']
    if file_format not in legal_formats:
        raise ValueError(f"Invalid format. Must be {', '.join(legal_formats[:-1])} or {legal_formats[-1]}")

    folder_path = os.path.dirname(filepath)
    if folder_path and not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    if file_format in ['pkl', 'psydat']: 
        with open(filepath, 'wb') as file:
            pkl.dump(data, file)

    elif file_format == 'json':
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=2)

    elif file_format == 'yaml':
        with open(filepath, 'w') as file:
            yaml.dump(data, file)

    elif file_format == 'csv':
        with open(filepath, 'w', newline='') as f:
            # Use dictwriter if list of dicts
            if data and isinstance(data[0], dict):
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            # Else use normal writer
            else: 
                writer = csv.writer(f)
            writer.writerows(data)