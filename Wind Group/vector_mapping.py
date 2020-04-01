import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
from netCDF4 import Dataset as netcdf_dataset


def real_data(filename):
    dataset = netcdf_dataset(filename, 'r')

    '''''
    for i in dataset.variables:
        print(i, dataset.variables[i].units, dataset.variables[i].shape)
    '''''

    x = dataset.variables['lon'][:]
    y = dataset.variables['lat'][:]
    u = dataset.variables['U'][0, 0, :, :]
    v = dataset.variables['V'][0, 0, :, :]

    X, Y = np.meshgrid(x, y)

    return X, Y, u, v


def main():

    x, y, u, v = real_data('../Data/wind/MERRA2.20050111.A3dyn.05x0625.EU.nc4')

    proj = ccrs.PlateCarree()

    color_array = np.sqrt(v ** 2 + u ** 2) - 2

    ax = plt.axes(projection=proj)  # create axes
    ax.coastlines(resolution='50m')
    ax.quiver(x, y, u, v, color_array, units='xy', alpha=0.8, pivot='tail', scale=20, headwidth=2, width=0.04)

    plt.show()


main()
