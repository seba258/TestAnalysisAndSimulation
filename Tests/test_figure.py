import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

filename = "../Data/Aerosol.24h.JAN.OFF.nc4"

DS = xr.open_dataset(filename)  # extract data set from netCFD file
da = DS.PM25  # retrieve data array containing 24h average PM25 concentrations (21 days, 72 levels)

pm25_gd_15 = da.sel(lev=1, method='nearest').sel(time='2005-1-15')[0]  # select appropriate level (ground) and day
pm25_gd_17 = da.sel(lev=1, method='nearest').sel(time='2005-1-17')[0]  # select appropriate level (ground) and day

proj = ccrs.PlateCarree()  # select projection. Only seems to work with PlateCarree though

ax = plt.axes([0.1, 0.55, 0.8, 0.4], projection=proj)  # create axes
ax.coastlines(resolution='50m')  # draw coastlines with given resolution

# plot data
ax.pcolormesh(da.lon, da.lat, pm25_gd_15, transform=proj)
ax.pcolormesh(da.lon, da.lat, pm25_gd_17, transform=proj)
pm25_gd_15.plot_map()

ax = plt.axes([0.1, 0.05, 0.8, 0.4], projection=proj)  # create axes
ax.coastlines(resolution='50m')  # draw coastlines with given resolution

# plot data
ax.pcolormesh(da.lon, da.lat, pm25_gd_17, transform=proj)
pm25_gd_17.plot_map()

plt.show()
