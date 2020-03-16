# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 09:58:30 2020

@author: Egon Beyne
"""

import numpy as np

"""
<<<<<<< HEAD

=======
>>>>>>> origin/master
"""
def Altitude_Conversion(h):
    # Import altitude level data
    alt_dat = np.genfromtxt("Altitude_levels.txt", skip_header = 3,usecols = (0,1,2))
    # Iterate through altitude table
    for i in range(len(alt_dat[:,2])-1):
        # Check if h is in interval
        if alt_dat[i, 2] >= h > alt_dat[i + 1, 2]:
            
            h_tab   = alt_dat[i,2]
            alt_num = alt_dat[i,1]
        # Values if h<1 km   
        elif h<1:
            h_tab = 0
            alt_num = 1
            
    return h_tab, alt_num

"""
def level_to_meter(level):
    alt_dat = np.genfromtxt("Altitude_levels.txt", skip_header = 3,usecols = (0,1,2))

    for i in range(len(alt_dat[:,2])-1):
        if alt_dat[i-1,1]<level and alt_dat[i,1]>=level:
            h_tab = alt_dat[i,2]
            alt_num = alt_dat[i,1]
    return h_tab
========
>>>>>>>> origin/master:Altitude_converter.py
=======

"""
# generate altitude in km from a given eta
def eta_to_altitude(h):
    # Import altitude level data
    alt_dat = np.genfromtxt("Altitude_levels.txt", skip_header=3, usecols=(0, 1, 2))
    # Iterate through altitude table
    altitude = min(alt_dat[:, 2])  # set to sea level
    for i in range(len(alt_dat[:, 1]) - 1):
        # Check if h is in interval
        if alt_dat[i, 1] <= h < alt_dat[i + 1, 1]:

            altitude = alt_dat[i, 2]

    return altitude


# generate eta from altitude in km
def altitude_to_eta(h):
    # Import altitude level data
    alt_dat = np.genfromtxt("Altitude_levels.txt", skip_header=3, usecols=(0, 1, 2))
    # Iterate through altitude table
    eta = max(alt_dat[:, 1])  # set to sea level
    for i in range(len(alt_dat[:, 2]) - 1):
        # Check if h is in interval
        if alt_dat[i, 2] >= h > alt_dat[i + 1, 2]:

            eta = alt_dat[i, 1]
        if h < 1:
            eta = max(alt_dat[:,1])

    return eta
