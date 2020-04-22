import tkinter as tk
from matplotlib import pyplot as plt, animation
import numpy as np
import cartopy.crs as ccrs
from GUI import Select_pollutant


def show_plot(da, level, time):
    if hasattr(da, 'lev') and level > 0:
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

def animate_plot(var,level):


    # Check if there are different altitude levels
    if hasattr(var, 'lev') and var.lev.values.size>1:

        da = getattr(var, "sel")(lev=level, method='nearest')

    else:
        da = var


    # select projection. Only seems to work with PlateCarree though
    proj = ccrs.PlateCarree()

    # Determine number of points in time

    n = da.time.size

    # Create subplot
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create axes and add map
    ax = plt.axes(projection=proj)  # create axes
    ax.coastlines(resolution='50m')  # draw coastlines with given resolution

    # Set color and scale of plot
    cax = da[0, :, :].plot_map(add_colorbar=True,
                               cmap='coolwarm',
                               vmin=da.values.min(),
                               vmax=da.values.max(),
                               cbar_kwargs={'extend': 'neither'})

    # Animation function
    def animate(frame):
        cax.set_array(da[frame, :, :].values.flatten())
        ax.set_title("Time = " +
                     str(da.coords["time"].values[frame])[:13])

    # Animate plots
    ani = animation.FuncAnimation(fig, animate,
                                  frames=n,
                                  interval=100)
    # Show plot
    plt.show()



running = True

while running:
    filepath, file_sub, lev, time, Anim_state = Select_pollutant()

    print(Anim_state)

    if Anim_state:
        animate_plot(filepath - file_sub, lev)
    else:
        show_plot(filepath - file_sub, lev, time)

