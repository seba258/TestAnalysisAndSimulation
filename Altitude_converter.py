# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 09:58:30 2020

@author: Egon Beyne
"""

import numpy as np


def Altitude_Conversion(h):
    # Import altitude level data
    alt_dat = np.genfromtxt("Altitude_levels.txt", skip_header = 3,usecols = (0,1,2))
    # Iterate through altitude table
    if not isinstance(h, list):
        h = [h]

    h_tab = []
    alt_num = []

    for i in range(len(h)):
        h_tab.append(0)
        alt_num.append(1)
        for j in range(len(alt_dat[:, 2]) - 1):
            # Check if h is in interval
            if alt_dat[j, 2] >= h[i] > alt_dat[j + 1, 2]:

                h_tab[i] = alt_dat[j, 2]
                alt_num[i] = alt_dat[j, 1]

    if len(h_tab) == 1:
        h_tab = h_tab[0]
        alt_num = alt_num[0]

    return h_tab, alt_num
