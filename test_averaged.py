import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

data_dir = "Data/"
output_dir = "Output/"

filename = "Aerosol.24h.JAN.OFF"

DS = xr.open_dataset(data_dir + filename + ".nc4")  # extract data set from netCFD file
da = DS.PM25  # retrieve data array containing 24h average PM25 concentrations (21 days, 72 levels)

proj = ccrs.PlateCarree()  # select projection. Only seems to work with PlateCarree though

frames = np.arange('2005-01-12', '2005-02-01', dtype='datetime64')

average = da.sel(lev=1, method='nearest').sel(time='2005-01-11')[0]

for frame in frames:
    average += da.sel(lev=1, method='nearest').sel(time=str(frame))[0]  # select appropriate level (ground) and day

average /= len(frames) + 1
ax = plt.axes(projection=proj)  # create axes
ax.coastlines(resolution='50m')  # draw coastlines with given resolution
average.plot()
plt.show()