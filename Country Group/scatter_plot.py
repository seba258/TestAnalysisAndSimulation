import country_tools as ct
import numpy as np
from matplotlib import pyplot as plt

"""
Scatter plot of all countries in the region, with emission and pollution axes

@author Jakob Schoser
"""

summer = True   # used to select between pollution data for January and July

poll_coll = "Soot.24h"  # the collection name for pollution (first part of the .nc4 filename)

# the chemicals to be taken into account for pollution and emissions, respectively. These need to be the names of the
# data sets inside the .nc4 files you selected
poll_chemical = "AerMassBC"
em_chemical = "BC"

em_mult = 1
poll_mult = 1

# the altitude levels over which emissions will be considered (available from 0 to 32). Check Altitude_levels.txt for
# conversion to km. Level 8: 1 km altitude, level 32: 13 km altitude
emission_levels = slice(0, 8)

method = ct.METHOD_AVG  # the way that the data is combined inside one country (median or area-weighted average)

print("Creating country polygons...")
countries = ct.create_country_polygons()

print("Retrieving raw pollution and emission data...")
raw_data, _ = ct.find_poll_em_data(countries, poll_coll, em_chemical, poll_chemical,
                                   emission_levels, summer)

print("Processing the data...")
em_data, _ = ct.process_data(countries, raw_data, method=method, mode=ct.PLOT_EMISSIONS, multiplier=em_mult)
poll_data, _ = ct.process_data(countries, raw_data, method=method, mode=ct.PLOT_POLLUTION, multiplier=poll_mult)

print("Plotting...")
em_values = np.array(list(em_data.values()))
poll_values = np.array(list(poll_data.values()))

plt.axis([min(em_values), max(em_values), min(poll_values), max(poll_values)])

plt.scatter(em_values, poll_values, cmap='hsv', c=np.random.rand(len(em_values)))

for country in em_data:
    plt.annotate(country, [em_data[country], poll_data[country]])

plt.title(ct.generate_sub_title(poll_chemical, em_chemical, summer, emission_levels, method))
plt.xlabel(em_chemical + " Emission Mass from Aviation $[kg/day/km^2]$")
plt.ylabel(("Average Ground-Level {} from Aviation " + "$[\mu g/m/km^2]$"
            if poll_chemical != "SpeciesConc_O3" else "$[mol/(mol of dry air)/km^2]$").format(poll_chemical))

print("Finished")
plt.show()
