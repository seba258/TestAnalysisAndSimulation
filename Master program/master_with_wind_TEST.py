import tkinter as tk
from GUI import Select_pollutant
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from netCDF4 import Dataset as netcdf_dataset
from matplotlib import animation
from matplotlib import rcParams


month = '01'
day = '20'

dataset = netcdf_dataset('../Data/wind/' + month + '/MERRA2.2005' + month + day + '.A3dyn.05x0625.EU.nc4')


def unpack_windposdata():
    # the 'lon' array is 1D with 129 entries. The 'lat' array is 1D with 81 entries.
    x = dataset.variables['lon'][:]
    y = dataset.variables['lat'][:]

    # the quiver() function requires all arrays to be the same size
    # therefore we convert x and y into 2D arrays X and Y
    X, Y = np.meshgrid(x, y)

    return X, Y


def unpack_windveldata(time):
    # the U and V array are both 4D. The first col is time, the second is lev, third and fourth are lat and lon.
    # we take the first time and first lev entry, which returns both u and v as 2D.
    u = dataset.variables['U'][time, 0, :, :]
    v = dataset.variables['V'][time, 0, :, :]

    return u, v


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


def animate_plot(var, level):

    # Check if there are different altitude levels
    if hasattr(var, 'lev') and var.lev.values.size>1:

        da = getattr(var, "sel")(lev=level, method='nearest')

    else:
        da = var

    X, Y = unpack_windposdata()
    U, V = unpack_windveldata(0)

    color_array = np.sqrt(V ** 2 + U ** 2)

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
    cax = da[0, :, :].plot(add_colorbar=False,
                           cmap='coolwarm',
                           vmin=da.values.min(),
                           vmax=da.values.max())

    Q = ax.quiver(X, Y, U, V, color='white', units='xy', alpha=0.8, pivot='tail', scale=20, headwidth=2, width=0.04)

    # Animation function
    def animate(frame, Q, X, Y):
        cax.set_array(da[frame*3, :, :].values.flatten())
        ax.set_title("Time = " +
                     str(da.coords["time"].values[frame])[:13])

        # updates the horizontal and vertical vector components
        U, V = unpack_windveldata(frame)
        Q.set_UVC(U, V)

        return Q,

    # Set up formatting for the movie files
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=1, metadata=dict(artist='Me'), bitrate=1800)

    # Animate plots
    ani = animation.FuncAnimation(fig, animate, fargs=(Q, X, Y), frames=8, interval=1000, blit=False, repeat=True)
    ani.save('PM25_wind.mp4', writer=writer)

    # Show plot
    plt.show()


running = True

while running:
    filepath, file_sub, lev, time, Anim_state = Select_pollutant()

    if Anim_state:
        animate_plot(filepath - file_sub, lev)
    else:
        show_plot(filepath - file_sub, lev, time)

