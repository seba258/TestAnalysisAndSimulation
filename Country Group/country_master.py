import cartopy.io.shapereader as shpreader
from shapely import geometry
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from descartes import PolygonPatch
from pprint import PrettyPrinter
from pyproj import Geod

"""
Shows map with colour coding for different statistics relating to aircraft emissions and ground pollution due to
aircraft. The available statistics are:
    - BC emissions of aircraft summed over a specified altitude range
    - BC ground pollution due to aircraft summed over 21 days (January or July)
    - Ratio of BC ground pollution to BC emissions due to aviation
In order to obtain a single value for the country, several methods of combining the per-grid-cell data are supported:
    - Area average, which sums the data over the entire area of the country and then divides by its surface area
    - Median, which takes the median of all values in the country
The user can select between summer and winter using a boolean and define the altitude ranges over which emissions are
considered (e.g. to separate cruise and LTO emissions). In addition to that, outlier countries can be specified to make
local differences more visible. Countries who cause a division by zero during the calculation (e.g. if the emissions
are zero in the ratio statistic) will automatically be removed. All removed countries are shown in black.

@author Jakob
"""

# Always keep in mind that the data for countries such as Russia and Algeria are only representative of the part of that
# country which lies within the data region (and not of the entire country)
# Also note that the pollution data is not influenced by areas outside of the data region (so the data does not show
# pollution caused in Western Europe by cruise emissions in the US)
# The numbers for emissions are often VERY small, in the order of 10^-14 to 10^-15. Be aware of machine precision
# AvEmMasses.nc4 can also be used instead of AvEmFluxes.nc4, but it does not contain any information about differences
# in altitudes. It merely contains the sum of all emissions over a certain grid cell

summer = False  # used to select between pollution data for January and July

# the altitude levels over which emissions will be considered. Check Altitude_levels.txt for conversion to km
# level 8: 1 km altitude, level 14: 2 km altitude
emission_levels = slice(1, 8)

# the value for these countries will be set to zero. That is useful if some countries have such high or low values that
# they make it impossible to see any differences between the other countries
outlier_countries = ["Iraq", "Israel", "Latvia"]

# available statistics for plotting
PLOT_RATIO = "Ground Pollution/Emission Ratio"
PLOT_EMISSIONS = "Emissions"
PLOT_POLLUTION = "Ground Pollution"

plotting_mode = PLOT_RATIO

# supported ways of summarising data in a country
METHOD_AVG = "Area average"
METHOD_MEDIAN = "Median"

method = METHOD_AVG

# the countries that are (partially) in the area for which we have data
interesting = [
    "Albania",
    "Andorra",
    "Armenia",
    "Austria",
    "Azerbaijan",
    "Belarus",
    "Belgium",
    "Bosnia and Herzegovina",
    "Bulgaria",
    "Croatia",
    "Cyprus",
    "Czechia",
    "Denmark",
    "Estonia",
    "Faroes",
    "Finland",
    "France",
    "Georgia",
    "Germany",
    "Gibraltar",
    "Greece",
    "Guernsey",
    "Hungary",
    "Iceland",
    "Ireland",
    "Isle of Man",
    "Italy",
    "Jersey",
    "Kazakhstan",
    "Kosovo",
    "Latvia",
    "Liechtenstein",
    "Lithuania",
    "Luxembourg",
    "Malta",
    "Moldova",
    "Monaco",
    "Montenegro",
    "Netherlands",
    "North Macedonia",
    "Norway",
    "Poland",
    "Portugal",
    "Romania",
    "Russian Federation",
    "San Marino",
    "Serbia",
    "Slovakia",
    "Slovenia",
    "Spain",
    "Sweden",
    "Svalbard and Jan Mayen",
    "Switzerland",
    "Turkey",
    "Ukraine",
    "United Kingdom",
    "Vatican City",
    "Morocco",
    "Algeria",
    "Tunisia",
    "Libya",
    "Egypt",
    "Syria",
    "Lebanon",
    "Jordan",
    "Israel",
    "Iraq",
    "Iran",
    "Saudi Arabia",
    "Palestine"
]

# data from 2016 for 1:20 million scale world map. More coarse or detailed maps are available. The coordinate
# system is with longitude and latitude in degrees
shape_file = 'Shapefiles/CNTR_RG_20M_2016_4326.shp'

# NetCDF files containing pollution with aircraft on and off, respectively
poll_on_filename = "Soot.24h.{}.ON.nc4".format("JUL" if summer else "JAN")
poll_off_filename = "Soot.24h.{}.OFF.nc4".format("JUL" if summer else "JAN")

em_filename = "AvEmFluxes.nc4"  # NetCDF file containing aircraft emissions
em_multiplier = 10E5  # factor to increase values of emission data and avoid rounding errors due to machine precision

colormap = "coolwarm"  # colour map
removed_colour = (0, 0, 0, 1)  # colour for removed countries

# create a dictionary containing the polygons for all countries listed in "interesting". This function returns a
# dictionary with the format "country_name: [[list of polygons that it is made up of], total area]"
def create_country_polygons():
    frame = geometry.Polygon([(-30, 30), (50, 30), (50, 70), (-30, 70)])  # the geographic area for which we have data
    geod = Geod('+a=6378137 +f=0.0033528106647475126')  # object used for conversion from degrees to km

    # read the shape file
    reader = shpreader.Reader(shape_file)

    # this is a generator, not a list. So you can only loop over it, not use indexing. But if necessary, it can be
    # converted using list( ).
    countries = reader.records()

    # the keys are country names (in English), and the value for each of them is a list with the polygons that the
    # country shape is made up of
    country_dict = {}

    # fill the country_dict
    for country in countries:
        # the .split( ) part in this statement is necessary because for some reason the names have \x00\x00\x00... added
        # to them. If you don't remove that, the statement doesn't find any of them in the "interesting" list
        country_name = country.attributes['NAME_ENGL'].split("\x00")[0]
        if country_name in interesting:
            # create empty list which will be filled with the polygons of the country, and set total area to 0
            country_dict[country_name] = [[], 0]
            multipolygon = country.geometry.geoms  # a multipolygon can consist of several disjoint polygons
            for polygon in multipolygon:  # each of these is a shapely polygon
                country_dict[country_name][0].append(polygon)
                # add the area of the country which lies inside of the frame (in km^2)
                country_dict[country_name][1] += abs(geod.geometry_area_perimeter(polygon.intersection(frame))[0] / 1E6)

    return country_dict


# find the name of the country in which the coordinates (lon, lat) lie. Return None if it does not lie inside any
# of the countries listed in "countries". "countries" has the same format as the return value of
# create_country_polygons(), i.e. a dictionary with country names as keys and lists of polygons as values
def find_country_name(countries, lon, lat):
    for name in countries:  # loop over all countries
        for region in countries[name][0]:  # loop over each polygon that the country is made of
            if region.contains(geometry.Point(lon, lat)):  # check if the polygon contains the coordinates
                return name
    return None


# find the ground level pollution (BC due to aircraft) and aircraft BC emission ratio for each country, and return it
# in a dictionary.
def find_poll_em_data(countries):
    DS = xr.open_dataset(em_filename)
    da_em = DS.BC * em_multiplier  # select only the BC (black carbon) emissions since it is inert

    DS_on = xr.open_dataset(poll_on_filename)
    DS_off = xr.open_dataset(poll_off_filename)

    # subtract pollution data without aircraft from pollution with aircraft to retrieve the pollution caused by
    # aircraft only. Also, only select BC
    da_poll = DS_on.AerMassBC - DS_off.AerMassBC

    poll_em_data = {}
    lon_axis = da_em.coords['lon'].values  # the longitude values of the data grid
    lat_axis = da_em.coords['lat'].values  # the latitude values of the data grid

    # this block fills poll_em_data in the format "country_name: [total_emissions, time_averaged_pollution]"
    for lon in lon_axis:
        for lat in lat_axis:  # loop over all cells in the data grid
            country = find_country_name(countries, lon, lat)  # find the country the cell lies in
            if country is not None:
                if country not in poll_em_data:
                    # if this is the first time the country is detected, set emission and pollution counters to 0
                    poll_em_data[country] = [[], []]
                # select the correct values from the simulation data and add it to the lists. Sum over all parameters
                # which are not explicitly specified (e.g. time or altitude)
                poll_em_data[country][0].append(np.sum(da_em.sel(lon=lon, lat=lat)
                                                       .sel(lev=emission_levels).values))  # select altitude range
                poll_em_data[country][1].append(np.sum(da_poll.sel(lon=lon, lat=lat)
                                                       .sel(lev=1, method='nearest').values))

    return poll_em_data


# functions to map the values for each country between 0 and 1
def lin_mapping(val, min_val, max_val):
    return (val - min_val) / (max_val - min_val)


def sqrt_mapping(val, min_val, max_val):
    return np.sqrt((val - min_val) / (max_val - min_val))


def log_mapping(val, min_val, max_val):
    return np.log((val - min_val) / (max_val - min_val) + 1) / np.log(2)


# show map with colour coding for the pollution and/or emission data
def plot(countries, poll_em_data, mode, method):
    data = poll_em_data.copy()  # make a copy of the data to not modify the original

    # summarise list of data for each country in one single value, using the selected method
    if method == METHOD_AVG:
        for country in poll_em_data:
            data[country] = np.sum(poll_em_data[country], axis=1)
    elif method == METHOD_MEDIAN:
        for country in poll_em_data:
            data[country] = np.median(poll_em_data[country], axis=1)
    else:
        print("Error: Invalid averaging method")

    # list of all countries that were removed, either if they lead to divisions by zero or because they were labelled
    # as outliers. This list does not contain the countries for which we do not have any data at all
    removed_countries = []

    # post-process the data according to the selected statistic to get the format "country_name: value"
    if mode == PLOT_RATIO:
        for country in poll_em_data:
            # avoid division by zero and check that the country isn't labeled as an outlier
            if data[country][0] != 0 and not any([outlier in country for outlier in outlier_countries]):
                data[country] = data[country][1] / data[country][0]  # divide pollution by emissions
            else:
                removed_countries.append(country)
                del data[country]
    elif mode == PLOT_EMISSIONS or mode == PLOT_POLLUTION:
        for country in poll_em_data:
            if not any([outlier in country for outlier in outlier_countries]):
                # divide pollution or emissions (depending on the mode) by the area of the corresponding country
                data[country] = data[country][0 if mode == PLOT_EMISSIONS else 1] / countries[country][1]
            else:
                removed_countries.append(country)
                del data[country]
    else:
        print("Error: Invalid mode for plotting")

    ax = plt.gca()  # get the axes of the current figure
    ax.set_title(mode + "\n\nConsidered chemical: BC | Time frame for pollution: " +
                 ("July" if summer else "January") + " 2005 | Altitude levels for emission: " +
                 str(emission_levels.start) + " to " + str(emission_levels.stop) + "| Averaging method: " + method)
    ax.set_xlabel("Removed countries: " + str(removed_countries))

    # only display the region for which we have data
    ax.set_xlim([-30, 50])
    ax.set_ylim([30, 70])

    # find maximum and minimum value to scale the colour coding
    min_val = min(data.values())
    max_val = max(data.values())

    # loop over all countries for which we have found a pollution and emission data. These are not necessarily the
    # same countries as the ones in the polygon dictionary, since some countries (e.g. Vatican City) are too small
    # to contain any data (the grid is too coarse). These countries will then not be plotted
    for name in data:
        value = data[name]  # retrieve the value for this country

        # select the colour based on the value. Nonlinear mappings are used to make differences more apparent
        colour = plt.get_cmap(colormap)(sqrt_mapping(value, min_val, max_val))
        for region in countries[name][0]:  # loop over all regions that the country consists of
            ax.plot(*region.exterior.xy, alpha=0)  # plot the borders of the polygon
            ax.add_patch(PolygonPatch(region, facecolor=colour))  # fill the polygon with colour

    for name in removed_countries:
        for region in countries[name][0]:  # loop over all regions that the country consists of
            ax.plot(*region.exterior.xy, alpha=0)  # plot the borders of the polygon
            ax.add_patch(PolygonPatch(region, facecolor=removed_colour))  # fill the polygon with colour

    return data, removed_countries


pp = PrettyPrinter(indent=4)
print("Creating country polygons...")
countries = create_country_polygons()
print("Retrieving pollution and emission data...")
poll_em_data = find_poll_em_data(countries)
print("Plotting...")
data, removed_countries = plot(countries, poll_em_data, plotting_mode, method)
print("Finished")
print("The following countries were removed:", removed_countries)
print("The resulting data is:")
pp.pprint(data)
plt.show()
