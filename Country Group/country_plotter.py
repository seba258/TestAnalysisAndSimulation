import country_tools as ct
import numpy as np
from matplotlib import pyplot as plt

summer = True   # used to select between pollution data for January and July

poll_coll = "Soot.24h"  # the collection name for pollution (first part of the .nc4 filename)

# the chemicals to be taken into account for pollution and emissions, respectively. These need to be the names of the
# data sets inside the .nc4 files you selected
poll_chemical = "AerMassBC"
em_chemical = "BC"

# the altitude levels over which emissions will be considered (available from 0 to 32). Check Altitude_levels.txt for
# conversion to km. Level 8: 1 km altitude, level 32: 13 km altitude
emission_levels = slice(0, 32)

# these countries will be ignored in the calculation. That is useful if some countries have such high or low values that
# they make it impossible to see any differences between the other countries
outliers = []  # ["Iraq", "Israel", "Latvia"]

method = ct.METHOD_AVG  # the way that the data is combined inside one country (median or area-weighted average)

print("Creating country polygons...")
countries = ct.create_country_polygons()

print("Retrieving raw pollution and emission data...")
raw_data, _ = ct.find_poll_em_data2(countries, poll_coll, em_chemical, poll_chemical,
                                   emission_levels, summer, recalculate_country_cells=True)

print("Processing the data...")
em_data, _ = ct.process_data(countries, raw_data, method=method, mode=ct.PLOT_EMISSIONS, multiplier=1E20)
poll_data, _ = ct.process_data(countries, raw_data, method=method, mode=ct.PLOT_POLLUTION, multiplier=1E9)

print("Plotting...")
em_values = np.array(list(em_data.values()))
poll_values = np.array(list(poll_data.values()))
plt.scatter(em_values, poll_values, cmap='hsv', c=np.random.rand(len(em_values)))

for country in em_data:
    plt.annotate(country, [em_data[country], poll_data[country]])

plt.xlabel("BC Emission Mass from Aviation [kg/day]")
plt.ylabel("Average Ground-Level BC Aerosol from Aviation [$\mu/m^3$]")

print("Finished")
plt.show()
