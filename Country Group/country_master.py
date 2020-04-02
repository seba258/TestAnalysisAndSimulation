import cartopy.io.shapereader as shpreader
from shapely import geometry
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from descartes import PolygonPatch
from pprint import PrettyPrinter

"""
Shows map with colour coding for the ground pollution over emission ratios per country. Only black carbon (BC) emissions
and pollution are considered. Apart from ratios, it can also plot only pollution or emissions, respectively.
The user can select between summer and winter (see boolean below) and the altitude ranges over which emissions are
considered (e.g. to separate cruise and LTO emissions).
The ratio of countries with no emissions over the considered altitude range is set to zero (the same is done for
countries the user can specify as outliers). Dark colours mean high values for the ratio, emissions or pollution,
depending on the selected mode.

@author Jakob
"""

# TODO: Calculate area of countries within data region to allow for area-normalised data (i.e. per sq. m, not degrees!)
# TODO: Plot ratio in higher resolution than just country level
# TODO: Allow user to select between mean/sum and median within countries
# Always keep in mind that the data for countries such as Russia and Algeria are only representative of the part of that
# country which lies within the data region (and not of the entire country)
# Also note that the pollution data is influenced by areas outside of the data region (e.g. emissions from the US
# reach Western Europe and cause pollution), while emission data is only from above Europe
# The numbers for emissions are often VERY small, in the order of 10^-14 to 10^-15. Is machine precision in issue?
# AvEmMasses.nc4 can also be used instead of AvEmFluxes.nc4, but it does not contain any information about differences
# in altitudes. It merely contains the sum of all emissions over a certain grid cell

summer = False  # used to select between pollution data for January and July

# the altitude levels over which emissions will be considered. Check Altitude_levels.txt for conversion to km
# Level 8: 1 km altitude, level 14: 2 km altitude
emission_levels = slice(1, 8)

# the value for these countries will be set to zero. That is useful if some countries have such high or low values that
# they make it impossible to see any differences between the other countries
outlier_countries = []  # ["Iraq", "Israel", "Latvia"]

MODE_RATIO = "Ground Pollution/Emission Ratio"
MODE_EMISSION = "Emissions"
MODE_POLLUTION = "Ground Pollution"

selected_mode = MODE_POLLUTION

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
em_multiplier = 10E5


# create a dictionary containing the polygons for all countries listed in "interesting". This function returns a
# dictionary with the format "country_name: [[list of polygons that it is made up of], total area]"
def create_country_polygons():
    # read the shape file
    reader = shpreader.Reader(shape_file)

    frame = geometry.Polygon([(-30, 30), (50, 30), (50, 70), (-30, 70)])

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
                country_dict[country_name][1] += polygon.intersection(frame).area

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


# find the ground level pollution (BC due to aircraft) to aircraft BC emission ratio for each country, and return it
# in a dictionary. Or return emission or pollution data only, if that is the selected mode
def find_poll_em_data(countries, mode):
    DS = xr.open_dataset(em_filename)
    da_em = DS.BC * em_multiplier  # select only the BC (black carbon) emissions since it is inert

    DS_on = xr.open_dataset(poll_on_filename)
    DS_off = xr.open_dataset(poll_off_filename)

    # subtract pollution data without aircraft from pollution with aircraft to retrieve the pollution caused by
    # aircraft only. Also, only select BC
    da_poll = DS_on.AerMassBC - DS_off.AerMassBC

    # find the number of time steps in the data, to allow for time averaging of the pollution data
    t_steps = len(da_poll.coords['time'].values)

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
                    poll_em_data[country] = [0, 0]
                # select the correct values from the simulation data and add it to the counters. Sum over all parameters
                # which are not explicitly specified (e.g. time or altitude)
                poll_em_data[country][0] += np.sum(da_em.sel(lon=lon, lat=lat)
                                                     .sel(lev=emission_levels).values)  # select altitude range
                poll_em_data[country][1] += np.sum(da_poll.sel(lon=lon, lat=lat)
                                                     .sel(lev=1, method='nearest').values) / t_steps

    # list of all countries that were removed, either if they had no emissions (which would lead to division by zero)
    # or because they were labelled as outliers. This list does not contain the countries for which we do not have
    # any data at all
    removed_countries = []

    # post-process the data according to mode to get the format "country_name: value"
    if mode == MODE_RATIO:
        for country in poll_em_data:
            # avoid division by zero and check that the country isn't labeled as an outlier
            if poll_em_data[country][0] != 0 and not any([outlier in country for outlier in outlier_countries]):
                poll_em_data[country] = poll_em_data[country][1] / poll_em_data[country][0]
            else:
                removed_countries.append(country)
                poll_em_data[country] = 0
    elif mode == MODE_EMISSION:
        for country in poll_em_data:
            if not any([outlier in country for outlier in outlier_countries]):
                poll_em_data[country] = poll_em_data[country][0]
            else:
                removed_countries.append(country)
                poll_em_data[country] = 0
    elif mode == MODE_POLLUTION:
        for country in poll_em_data:
            if not any([outlier in country for outlier in outlier_countries]):
                poll_em_data[country] = poll_em_data[country][1]
            else:
                removed_countries.append(country)
                poll_em_data[country] = 0
    else:
        print("Error: Invalid mode for pollution and emission data retrieval")

    return poll_em_data, removed_countries


def sqrt_mapping(val, min_val, max_val):
    return 1 - np.sqrt((val - min_val) / (max_val - min_val))


def log_mapping(val, min_val, max_val):
    return 1 - np.log((val - min_val) / (max_val - min_val) + 1) / np.log(2)


# show map with colour coding for the pollution and/or emission data
def plot(countries, poll_em_data, mode):
    ax = plt.gca()  # get the axes of the current figure
    ax.set_title(mode + "\n\nConsidered chemical: BC | Time frame for pollution: " +
                 ("July" if summer else "January") + " 2005 | Altitude levels for emission: " +
                 str(emission_levels.start) + " to " + str(emission_levels.stop))
    ax.set_xlabel("Removed countries: " + str(removed_countries))

    # only display the region for which we have data
    ax.set_xlim([-30, 50])
    ax.set_ylim([30, 70])

    if mode != MODE_RATIO:
        for name in poll_em_data:
            poll_em_data[name] /= countries[name][1]

    # find maximum and minimum value to scale the colour coding
    min_val = min(poll_em_data.values())
    max_val = max(poll_em_data.values())

    # loop over all countries for which we have found a pollution and emission data. These are not necessarily the
    # same countries as the ones in the polygon dictionary, since some countries (e.g. Vatican City) are too small
    # to contain any data (the grid is too coarse). These countries will then not be plotted
    for name in poll_em_data:
        value = poll_em_data[name]  # retrieve the value for this country

        # select the colour based on the value. Darker colours mean a higher value (e.g. more ground level pollution
        # for the same amount of emissions). The mapping from value to colour is based on the square root since that
        # makes the differences more obvious than a linear mapping
        colour = sqrt_mapping(value, min_val, max_val)
        for region in countries[name][0]:  # loop over all regions that the country consists of
            ax.plot(*region.exterior.xy, alpha=0)  # plot the borders of the polygon
            ax.add_patch(PolygonPatch(region, facecolor=(colour, colour, colour)))  # fill the polygon with colour


pp = PrettyPrinter(indent=4)
print("Creating country polygons...")
countries = create_country_polygons()
print("Retrieving pollution and emission data...")
poll_em_data, removed_countries = find_poll_em_data(countries, selected_mode)
print("Plotting...")
plot(countries, poll_em_data, selected_mode)
print("Finished")
print("The following countries were removed:", removed_countries)
print("The resulting data is:")
pp.pprint(poll_em_data)
plt.show()
