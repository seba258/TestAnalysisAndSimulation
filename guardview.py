from math import *
import numpy as np
import pygame as pg
import time

def closescr():

    keys = pg.key.get_pressed()
    # Check for quit event (closing of window)
    for event in pg.event.get():
        if event.type==pg.QUIT:
            pg.quit()

    # Escape key check
    if keys[pg.K_ESCAPE]:
        pg.quit()

def initscr(xmax,ymax):
   
    # Define a pygame window
    
    reso = (xmax,ymax)
    scr = pg.display.set_mode(reso)
    # Fill screen with white
    #white = (255,255,255)
    #scr.fill(white)
   
    
    pg.display.set_caption("My Game of Life")

    
    return scr

    
def show(board):

    flip = pg.display.flip()
    return True

# Make board
scale = 2000
nx = 16*scale     #number of cells in x direction
ny = 3*scale   #number of cells in y direction
board = np.zeros((ny,nx))

# Initiate screen of x,y pixels
pg.init()
xmax = 800
ymax = 150
scr = initscr(xmax,ymax)

# Location guards (should be random and not on walls/boxes)
xguard = 16000
yguard = 500

# Location walls/boxes
xw1, yw1 = 2.15, 0.5
xw2, yw2 = 13.85, 0.5
xw3, yw3 = 4.5, 2.5
xw4, yw4 = 11.5, 2.5

wallarray = np.array([[xw1, yw1], [xw2, yw2], [xw3, yw3], [xw4, yw4]])
walls = wallarray*scale

# Calculation of angle between walls



# Calculation of distance between walls



# For every location, check if it is between the angle
# If it is, guard can't see it when distance is higher than wall distance



# Show board with pattern
show(board)

# Event pump
pg.event.pump()


# Close screen when escape or cross is pressed
close = closescr()




