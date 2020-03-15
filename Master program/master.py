import tkinter as tk
from matplotlib import pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from GUI import Select_pollutant


def show_plot(variable, level, time):
    da = getattr(getattr(variable, "sel")(lev=level, method='nearest'), "sel")(time=time)
    proj = ccrs.PlateCarree()

    # Create axes and add map
    ax = plt.axes(projection=proj)  # create axes
    ax.coastlines(resolution='50m')  # draw coastlines with given resolution

    # Set color and scale of plot
    da[0, :, :].plot(add_colorbar=True, cmap='coolwarm', vmin=da.values.min(), vmax=da.values.max(),
                     cbar_kwargs={'extend': 'neither'})

    plt.show()


running = True

while running:
    filepath, DS = Select_pollutant()
    print(filepath, DS)
    show_plot(filepath, 1, '2005-1-17')