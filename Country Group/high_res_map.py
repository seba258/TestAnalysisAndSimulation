import country_tools as ct
from cartopy import crs
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt

summer = True  # used to select between pollution data for January and July

# the altitude levels over which emissions will be considered. Check Altitude_levels.txt for conversion to km
emission_levels = slice(1, 32)

# NetCDF files containing pollution with aircraft on and off, respectively
poll_on_filename = ct.data_dir() / "Soot.24h.{}.ON.nc4".format("JUL" if summer else "JAN")
poll_off_filename = ct.data_dir() / "Soot.24h.{}.OFF.nc4".format("JUL" if summer else "JAN")

em_filename = ct.data_dir() / "AvEmFluxes.nc4"  # NetCDF file containing aircraft emissions

poll_on_DS = xr.open_dataset(poll_on_filename)
poll_off_DS = xr.open_dataset(poll_off_filename)
poll_da = (poll_on_DS.AerMassBC - poll_off_DS.AerMassBC).sel(lev=1, method='nearest').sum(dim='time')

em_DS = xr.open_dataset(em_filename)
em_da = em_DS.BC.sel(lev=emission_levels).sum(dim='lev')

ratio_da = poll_da / em_da
ratio_da = np.log(ratio_da)

proj = crs.PlateCarree()
ax = plt.axes(projection=proj)
ax.coastlines(resolution='50m')
ratio_da.plot()

plt.show()
