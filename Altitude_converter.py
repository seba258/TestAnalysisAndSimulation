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
    for i in range(len(alt_dat[:,2])-1):
        # Check if h is in interval
        if alt_dat[i,2]>= h and alt_dat[i+1,2]<h:
            
            h_tab   = alt_dat[i,2]
            alt_num = alt_dat[i,1]
        # Values if h<1 km   
        elif h<1:
            h_tab = 0
            alt_num = 1
            
    return h_tab, alt_num

print(Altitude_Conversion(0))