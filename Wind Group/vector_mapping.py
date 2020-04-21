import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from netCDF4 import Dataset as netcdf_dataset
from matplotlib import animation

test = '../Data/wind/MERRA2.20050111.A3dyn.05x0625.EU.nc4'
m = '01'
d = '11'


def unpack_data(month, day, time):
    dataset = netcdf_dataset('../Data/wind/' + month + '/MERRA2.2005' + month + day + '.A3dyn.05x0625.EU.nc4')

    # the 'lon' array is 1D with 129 entries. The 'lat' array is 1D with 81 entries.
    x = dataset.variables['lon'][:]
    y = dataset.variables['lat'][:]
    # the U and V array are both 4D. The first col is time, the second is lev, third and fourth are lat and lon.
    # we take the first time and first lev entry, which returns both u and v as 2D.
    u = dataset.variables['U'][time, 0, :, :]
    v = dataset.variables['V'][time, 0, :, :]

    # the quiver() function requires all arrays to be the same size
    # therefore we convert x and y into 2D arrays X and Y
    X, Y = np.meshgrid(x, y)

    n = np.size(dataset.variables['U'][:, 0, 0, 0])

    return X, Y, u, v, n


def main():
    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines(resolution='50m')

    x, y, u, v, n = unpack_data(m, d, 0)

    color_array = np.sqrt(v ** 2 + u ** 2)
    ax.quiver(x, y, u, v, color_array, units='xy', alpha=0.8, pivot='tail', scale=20, headwidth=2, width=0.04)

    plt.show()


main()
