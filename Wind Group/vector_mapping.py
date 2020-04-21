import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from netCDF4 import Dataset as netcdf_dataset
from matplotlib import animation

test = '../Data/wind/MERRA2.20050111.A3dyn.05x0625.EU.nc4'
month = '01'
day = '20'

dataset = netcdf_dataset('../Data/wind/' + month + '/MERRA2.2005' + month + day + '.A3dyn.05x0625.EU.nc4')


def unpack_posdata():
    # the 'lon' array is 1D with 129 entries. The 'lat' array is 1D with 81 entries.
    x = dataset.variables['lon'][:]
    y = dataset.variables['lat'][:]

    # the quiver() function requires all arrays to be the same size
    # therefore we convert x and y into 2D arrays X and Y
    X, Y = np.meshgrid(x, y)

    return X, Y


def unpack_veldata(time):
    # the U and V array are both 4D. The first col is time, the second is lev, third and fourth are lat and lon.
    # we take the first time and first lev entry, which returns both u and v as 2D.
    u = dataset.variables['U'][time, 0, :, :]
    v = dataset.variables['V'][time, 0, :, :]

    return u, v


def main():
    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines(resolution='50m')

    X, Y = unpack_posdata()
    U, V = unpack_veldata(0)

    color_array = np.sqrt(V ** 2 + U ** 2)
    Q = ax.quiver(X, Y, U, V, color_array, units='xy', alpha=0.8, pivot='tail', scale=20, headwidth=2, width=0.04)

    def update_quiver(time, Q, X, Y):
        # updates the horizontal and vertical vector components
        U, V = unpack_veldata(time)
        Q.set_UVC(U, V)

        return Q,

    # you need to set blit=False, or the first set of arrows never gets cleared on subsequent frames
    anim = animation.FuncAnimation(fig, update_quiver, fargs=(Q, X, Y), interval=1000, blit=False)

    plt.show()


main()
