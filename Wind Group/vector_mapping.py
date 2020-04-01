import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
from netCDF4 import Dataset as netcdf_dataset


def extract_data(filename):
    dataset = netcdf_dataset(filename, 'r')

    '''''
    for i in dataset.variables:
        print(i, dataset.variables[i].units, dataset.variables[i].shape)
    '''''

    # the 'lon' array is 1D with 129 entries. The 'lat' array is 1D with 81 entries.
    x = dataset.variables['lon'][:]
    y = dataset.variables['lat'][:]
    # the U and V array are both 4D. The first col is time, the second is lev, third and fourth are lat and lon.
    # we take the first time and lev entry, which returns both u and v as 2D.
    u = dataset.variables['U'][0, 0, :, :]
    v = dataset.variables['V'][0, 0, :, :]

    # the quiver() function requires all arrays to be the same size
    # therefore we convert x and y into 2D arrays X and Y
    X, Y = np.meshgrid(x, y)

    return X, Y, u, v


def main():
    x, y, u, v = extract_data('../Data/wind/MERRA2.20050111.A3dyn.05x0625.EU.nc4')

    proj = ccrs.PlateCarree()

    # color based on wind magnitude
    color_array = np.sqrt(v ** 2 + u ** 2)

    ax = plt.axes(projection=proj)
    ax.coastlines(resolution='50m')
    ax.quiver(x, y, u, v, color_array, units='xy', alpha=0.8, pivot='tail', scale=20, headwidth=2, width=0.04)

    plt.show()


main()
