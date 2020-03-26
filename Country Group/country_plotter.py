import json
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt

# TODO: Average or sum pollution values over time
# TODO: Verify that all grid cells are indeed the same size
# TODO: Draw map with colour coding for the pollution/emission ratio
# TODO: Compare winter data with summer data

poll_on_filename = "Soot.24h.JAN.ON.nc4"
poll_off_filename = "Soot.24h.JAN.OFF.nc4"
em_filename = "AvEmMasses.nc4"
countries_filename = "country_coords.txt"

print("Loading files...")

with open(countries_filename) as country_file:
    country_coords = json.loads(country_file.read())

DS = xr.open_dataset(em_filename)
da_em = DS.BC

DS_on = xr.open_dataset(poll_on_filename)
DS_off = xr.open_dataset(poll_off_filename)
da_poll = DS_on.AerMassBC - DS_off.AerMassBC
t_steps = len(da_poll.coords['time'].values)

print("Processing...")
data = {}

for country in country_coords:
    data[country] = np.zeros(2)
    for cell in np.array(country_coords[country]):
        data[country][0] += np.sum(da_em.sel(lon=cell[0], lat=cell[1]).values)
        data[country][1] += np.sum(da_poll.sel(lon=cell[0], lat=cell[1]).sel(lev=1, method='nearest').values) / t_steps

print("Plotting...")
plt.subplot(211)
values = np.array(list(data.values()))
plt.scatter(values[:, 0], values[:, 1], cmap='hsv', c=np.random.rand(len(data)))

for country in data:
    plt.annotate(country, data[country])

plt.xlabel("BC Emission Mass from Aviation [kg/day]")
plt.ylabel("Average Ground-Level BC Aerosol from Aviation [$\mu/m^3$]")

plt.subplot(212)
plt.bar(range(len(data)), values[:, 1] / values[:, 0], align='center')
plt.xticks(range(len(data)), data.keys())

plt.ylabel("BC Pollution/Emission")

print("Finished")
plt.show()
