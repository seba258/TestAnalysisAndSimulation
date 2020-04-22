import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

data_dir = "Data/"
output_dir = "Output/"

filename = "Aerosol.24h.JAN.OFF"

DS = xr.open_dataset(data_dir + filename + ".nc4")  # extract data set from netCFD file
da = DS.PM25  # retrieve data array containing 24h average PM25 concentrations (21 days, 72 levels)
pm25_gd = da.sel(lev=1, method='nearest').sel(time='2005-1-15')[0]  # select appropriate level (ground) and day

proj = ccrs.PlateCarree()  # select projection. Only seems to work with PlateCarree though

frames = np.arange('2005-01-11', '2005-02-01', dtype='datetime64')

for frame in frames:
    plt.clf()
    ax = plt.axes(projection=proj)  # create axes
    ax.coastlines(resolution='50m')  # draw coastlines with given resolution
    pm25_gd = da.sel(lev=1, method='nearest').sel(time=str(frame))[0]  # select appropriate level (ground) and day
    pm25_gd.plot_map(vmin=0, vmax=130)
    plt.savefig(output_dir + filename + "_" + str(frame) + ".png")
