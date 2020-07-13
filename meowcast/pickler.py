#!/usr/bin/env python 


import os
import pickle


def save_meow(meow):
    """
    save a meow object to a pickle
    """

    pickle_name = meow.location + ".pkl"
    with open(pickle_name, 'wb') as pkl:
        pickle.dump(meow, pkl)


def load_meow(location):
    """
    load a saved meow object
    """
    import time
    pickle_name = location + ".pkl"

    try:
        pickle_age = (time.time() - os.path.getatime(pickle_name)) / 60
        with open(pickle_name, 'rb') as pkl:
            meow = pickle.load(pkl)
        return meow, pickle_age
    except Exception as e:
        return None, None

