import tkinter as tk
from matplotlib import pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from GUI import Select_pollutant


def show_plot(da, level, time):
    if level > 0:
        da = getattr(da, "sel")(lev=level, method='nearest')
    if len(time) > 0:
        da = getattr(da, "sel")(time=time)
    proj = ccrs.PlateCarree()

    # Create axes and add map
    ax = plt.axes(projection=proj)  # create axes
    ax.coastlines(resolution='50m')  # draw coastlines with given resolution

    # Set color and scale of plot
    da.plot(add_colorbar=True, cmap='coolwarm', vmin=da.values.min(), vmax=da.values.max(),
            cbar_kwargs={'extend': 'neither'})

    plt.show()


running = True

while running:
    filepath, lev, time = Select_pollutant()
    show_plot(filepath, lev, time)
