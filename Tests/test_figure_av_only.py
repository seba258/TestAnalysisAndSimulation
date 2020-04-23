import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

filename_off = "../Data/Aerosol.24h.JAN.OFF.nc4"
filename_on = "../Data/Aerosol.24h.JAN.ON.nc4"

DS_off = xr.open_dataset(filename_off)  # extract data set from netCFD file
da_off = DS_off.PM25  # retrieve data array containing 24h average PM25 concentrations (21 days, 72 levels)

DS_on = xr.open_dataset(filename_on)  # extract data set from netCFD file
da_on = DS_on.PM25  # retrieve data array containing 24h average PM25 concentrations (21 days, 72 levels)

pm25_gd_off = da_off.sel(lev=1, method='nearest').sel(time='2005-01-15')[0]  # select appropriate level (ground) and day
pm25_gd_on = da_on.sel(lev=1, method='nearest').sel(time='2005-01-15')[0]  # select appropriate level (ground) and day

proj = ccrs.PlateCarree()  # select projection. Only seems to work with PlateCarree though

ax = plt.axes(projection=proj)  # create axes
ax.coastlines(resolution='50m')  # draw coastlines with given resolution

av_data = pm25_gd_on - pm25_gd_off

# plot data
#ax.pcolormesh(da_off.lon, da_off.lat, av_data, transform=proj)
av_data.plot_map(add_colorbar=True, cmap='coolwarm', vmin=av_data.values.min(), vmax=av_data.values.max(),
                 cbar_kwargs={'extend': 'neither'})

plt.show()
