from collections import OrderedDict
import cartopy.io.shapereader as shpreader
from shapely import geometry
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from descartes import PolygonPatch
from pprint import PrettyPrinter
from pyproj import Geod, Transformer
import json

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

In addition to a map displaying the data per country, the program outputs three indicators of spatial auto correlation:
Geary's C and global and local Moran's I. Global statistics are printed as a single value, while local statistics are
shown in a map

@author Jakob
"""

# TODO: Find neater solution for options
# TODO: Add colour bar
# Always keep in mind that the data for countries such as Russia and Algeria are only representative of the part of that
# country which lies within the data region (and not of the entire country)
# Also note that the pollution data is not influenced by areas outside of the data region (so the data does not show
# pollution caused in Western Europe by cruise emissions in the US)
# The numbers for emissions are often VERY small, in the order of 10^-14 to 10^-15. Be aware of machine precision
# AvEmMasses.nc4 can also be used instead of AvEmFluxes.nc4, but it does not contain any information about differences
# in altitudes. It merely contains the sum of all emissions over a certain grid cell

summer = True   # used to select between pollution data for January and July

# if set to False, the program looks for a file that already contains the pollution and emission data. If such a file
# does not exist for the selected settings, it still recalculates the data
recalculate_data = False

# the altitude levels over which emissions will be considered. Check Altitude_levels.txt for conversion to km
# level 8: 1 km altitude, level 14: 2 km altitude
emission_levels = slice(0, 8)

# the value for these countries will be set to zero. That is useful if some countries have such high or low values that
# they make it impossible to see any differences between the other countries
outliers = ["Iraq", "Israel", "Latvia"]

# available statistics for plotting
PLOT_RATIO = "Ground Pollution/Emission Ratio"
PLOT_EMISSIONS = "Emissions"
PLOT_POLLUTION = "Ground Pollution"

mode = PLOT_RATIO

# supported ways of summarising data in a country
METHOD_AVG = "Area average"
METHOD_MEDIAN = "Median"

method = METHOD_AVG

country_file = json.load(open("countries.json"))

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


# create a dictionary containing the polygons for all countries listed in "interesting". This function returns an
# ordered dictionary with the format "country_name: [[list of polygons that it is made up of], total area]"
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
    country_poly = {}

    # fill the country_poly
    for country in countries:
        # the .split( ) part in this statement is necessary because for some reason the names have \x00\x00\x00... added
        # to them. If you don't remove that, the statement doesn't find any of them in the "interesting" list
        country_name = country.attributes['NAME_ENGL'].split("\x00")[0]
        if country_name in country_file:
            # create empty list which will be filled with the polygons of the country, and set total area to 0
            country_poly[country_name] = [[], 0]
            multipolygon = country.geometry.geoms  # a multipolygon can consist of several disjoint polygons
            for polygon in multipolygon:  # each of these is a shapely polygon
                # get the portion of the polygon that's inside the data frame. This may result in shapely polygons or
                # multipolygons being created (e.g. if the original polygon is split in half)
                inside_frame = polygon.intersection(frame)

                # function used to add a polygon to the dictionary
                def add_region(region):
                    country_poly[country_name][0].append(region)
                    # add the area of the country which lies inside of the frame (in km^2)
                    country_poly[country_name][1] += abs(geod.geometry_area_perimeter(region)[0] / 1E6)

                if isinstance(inside_frame, geometry.Polygon) and not inside_frame.is_empty:
                    add_region(inside_frame)

                elif isinstance(inside_frame, geometry.MultiPolygon) and not inside_frame.is_empty:
                    for region in inside_frame:  # loop over all the polygons that make up the multipolygon
                        add_region(region)

            # eliminate any countries that don't have any polygons inside of the data frame
            if not country_poly[country_name][0]:
                del country_poly[country_name]

    # return an ordered dictionary (countries in alphabetical order)
    return OrderedDict(sorted(country_poly.items(), key=lambda t: t[0]))


# find the name of the country in which the coordinates (lon, lat) lie. Return None if it does not lie inside any
# of the countries listed in "countries". "countries" has the same format as the return value of
# create_country_polygons(), i.e. a dictionary with country names as keys and lists of polygons as values
def find_country_name(country_polygons, lon, lat):
    for name in country_polygons:  # loop over all countries
        for region in country_polygons[name][0]:  # loop over each polygon that the country is made of
            if region.contains(geometry.Point(lon, lat)):  # check if the polygon contains the coordinates
                return name
    return None


# find the ground level pollution (BC due to aircraft) and aircraft BC emission data for each country, and return it
# in an ordered dictionary in the form "country_name: [emission, pollution]".
def find_poll_em_data(country_polygons):
    if not recalculate_data:
        try:  # try and find a buffer file for the given settings
            poll_em_data = json.load(open("poll_em_buffer.json"))

            # retrieve the relevant parameters that were used to generate the buffer file
            summer_saved = poll_em_data["summer"]
            emission_levels_saved = poll_em_data["emission_levels"]

            # if time of year and altitude ranges match
            if summer_saved == summer and emission_levels_saved[0] == emission_levels.start and \
                    emission_levels_saved[1] == emission_levels.stop:

                # remove the items that stored parameters, since they are not needed anymore
                del poll_em_data["summer"]
                del poll_em_data["emission_levels"]

                # check for any missing countries in the file
                requested_keys = set(country_polygons.keys())
                returned_keys = set(poll_em_data.keys())
                unavailable = list(requested_keys.difference(returned_keys))

                print("Retrieved data from existing file")

                # return data, along with the names of all missing countries
                return OrderedDict(sorted(poll_em_data.items(), key=lambda t: t[0])), unavailable  # continue here

            else:  # if the settings in the buffer file don't match the required settings
                print("Parameters in buffer file don't match user input. Recalculating data...")

        except (FileNotFoundError, KeyError):  # in case there is no buffer file
            print("No valid file found, recalculating data...")

    # anything from here onwards is only executed in case the data needs to be recalculated

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
            country = find_country_name(country_polygons, lon, lat)  # find the country the cell lies in
            if country is not None:
                if country not in poll_em_data:
                    # if this is the first time the country is detected, set emission and pollution counters to 0
                    poll_em_data[country] = [[], []]
                # select the correct values from the simulation data and add it to the lists. Sum over all parameters
                # which are not explicitly specified (e.g. time or altitude)
                poll_em_data[country][0].append(float(np.sum(da_em.sel(lon=lon, lat=lat)
                                                       .sel(lev=emission_levels).values)))  # select altitude range
                poll_em_data[country][1].append(float(np.sum(da_poll.sel(lon=lon, lat=lat)
                                                       .sel(lev=1, method='nearest').values)))

    # write the data into a buffer file, to speed up loading next time the program is run
    with open("poll_em_buffer.json", "w") as outfile:
        data_saved = poll_em_data.copy()  # make a copy so that the original remains unchanged

        # add items describing the settings used to generate the data
        data_saved["summer"] = summer
        data_saved["emission_levels"] = [emission_levels.start, emission_levels.stop]

        # write the file
        json.dump(data_saved, outfile, indent=4)

    # check for any missing countries in the file
    requested_keys = set(country_polygons.keys())
    returned_keys = set(poll_em_data.keys())
    unavailable = list(requested_keys.difference(returned_keys))

    # return data, along with the names of all missing countries
    return OrderedDict(sorted(poll_em_data.items(), key=lambda t: t[0])), unavailable


# integrate the data over the country surfaces using the chosen method, and combine emission and pollution data
# according to the selected mode. Returns an ordered dict with "country_name: value". Also returns any countries that
# were removed
def process_data(country_polygons, raw_data):
    processed_data = raw_data.copy()  # make a copy of the data to not modify the original

    # summarise list of data for each country in one single value, using the selected method
    if method == METHOD_AVG:
        for country in raw_data:
            processed_data[country] = np.sum(raw_data[country], axis=1)
    elif method == METHOD_MEDIAN:
        for country in raw_data:
            processed_data[country] = np.median(raw_data[country], axis=1)
    else:
        print("Error: Invalid averaging method:", method)

    # list of all countries that were removed, either if they lead to divisions by zero or because they were labelled
    # as outliers. This list does not contain the countries for which we do not have any data at all
    removed_countries = []

    # post-process the data according to the selected statistic to get the format "country_name: value"
    if mode == PLOT_RATIO:
        for country in raw_data:
            # avoid division by zero and check that the country isn't labeled as an outlier
            if processed_data[country][0] != 0 and not any([outlier in country for outlier in outliers]):
                # divide pollution by emissions
                processed_data[country] = processed_data[country][1] / processed_data[country][0]
            else:  # remove the country from the data set if it is an outlier or if it has no emissions
                removed_countries.append(country)
                del processed_data[country]
    elif mode == PLOT_EMISSIONS or mode == PLOT_POLLUTION:
        for country in raw_data:
            if not any([outlier in country for outlier in outliers]):
                # divide pollution or emissions (depending on the mode) by the area of the corresponding country
                processed_data[country] = processed_data[country][0 if mode == PLOT_EMISSIONS else 1] / \
                                          country_polygons[country][1]
            else:  # remove the country from the data set if it is an outlier
                removed_countries.append(country)
                del processed_data[country]
    else:
        print("Error: Invalid mode:", mode)

    return OrderedDict(sorted(processed_data.items(), key=lambda t: t[0])), removed_countries


# returns a matrix that gives the spatial correlation between countries (based on the inverse of the distance between
# them). Used for spatial autocorrelation measurement
def spatial_matrix(country_polygons):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035")  # used to transform longitude and latitude to metres
    centres = []  # list for the centres of all countries
    for country in country_polygons:
        # the centre of the country is the weighted average of the centres of its sub-regions
        centre_lon_lat = sum([np.array(region.centroid) * region.area for region in country_polygons[country][0]]) / \
                         sum([region.area for region in country_polygons[country][0]])
        centres.append(transformer.transform(centre_lon_lat[0], centre_lon_lat[1]))  # transform centre to metres

    centres = np.array(centres) / 1E3  # convert centre coordinates from metres to kilometres
    polygon_values = list(country_polygons.values())  # values of the polygon list (used to get area of the country)
    w = np.zeros((len(country_polygons), len(country_polygons)))  # empty matrix for weights
    # loop over all rows of the matrix, each corresponding to a country
    for i in range(len(w)):
        # characteristic radius of the country (radius of a circle with the same area)
        char_rad = np.sqrt(polygon_values[i][1] / np.pi)

        distances = np.linalg.norm(centres[i] - centres, axis=1)  # distances from this country to all others
        distances[i] = 1  # avoid division by zero (distance from the country to itself is 0)

        # weight of each country is the inverse of its distance, multiplied by the current country's characteristic
        # radius This scaling is done because the influence of a big country at its borders is just as big as the
        # influence of a small country at its borders. If we didn't use this factor, the weight of the neighbouring
        # countries of a big country would be smaller, since they are further away from its centre.
        w[i] = 1 / distances * char_rad

        w[i, i] = 0  # set the weight of the current country w.r.t itself to 0

    return w


# return the global Moran's I for the data set. A positive value indicates that values are clustered, i.e. similar
# values are close to each other on the map (positive spatial auto correlation). A negative value means that similar
# values are far apart, and zero means that values are randomly distributed (negative spatial auto correlation)
def morans_i_global(country_polygons, data):
    w = spatial_matrix(country_polygons)

    data_values = list(data.values())
    mean = np.mean(data_values)
    s = 0
    for i in range(len(w)):
        for j in range(len(w[i])):
            s += w[i, j] * (data_values[i] - mean) * (data_values[j] - mean)

    return len(data_values) / np.sum(w) * s / np.var(data_values)


# return the Geary's C for the data set. A value between 0 and 1 indicates positive spatial auto correlation,
# a value larger than 1 shows negative spatial auto correlation. More sensitive to local scales than Moran's I
def gearys_c(country_polygons, data):
    w = spatial_matrix(country_polygons)

    data_values = list(data.values())
    s = 0
    for i in range(len(w)):
        for j in range(len(w[i])):
            s += w[i, j] * (data_values[i] - data_values[j]) ** 2

    return (len(data_values) - 1) * s / (2 * np.sum(w) * np.var(data_values))


# return the local Moran's I for each country in the data set. A positive value indicates that the country's value is
# similar to its neighbours, while a negative value shows that it is an outlier compared to its surroundings.
def morans_i_local(country_polygons, data):
    w = spatial_matrix(country_polygons)
    data_values = list(data.values())
    mean = np.mean(data_values)
    i_local = []
    for i in range(len(w)):
        var = np.mean(np.delete(data_values, i))
        s = 0
        for j in range(len(w[i])):
            s += w[i, j] * (data_values[j] - mean)
        i_local.append((len(w) - 1) / var * (data_values[i] - mean) * s / np.sum(w[i]))

    country_names = list(country_polygons.keys())
    return OrderedDict({country_names[i]: i_local[i] for i in range(len(w))})


# functions to map the values for each country between 0 and 1
def lin_mapping(val, min_val, max_val):
    return (val - min_val) / (max_val - min_val)


def sqrt_mapping(val, min_val, max_val):
    return np.sqrt((val - min_val) / (max_val - min_val))


def log_mapping(val, min_val, max_val):
    return np.log((val - min_val) / (max_val - min_val) + 1) / np.log(2)


# show map with colour coding for the pollution and/or emission data
def plot(country_polygons, processed_data, add_title="", add_info="", show_removed=False, mapping=lin_mapping):
    ax = plt.gca()  # get the axes of the current figure
    ax.set_title(mode + add_title + "\n\nConsidered chemical: BC | Time frame for pollution: " +
                 ("July" if summer else "January") + " 2005 | Altitude levels for emission: " +
                 str(emission_levels.start) + " to " + str(emission_levels.stop) + " | Averaging method: " + method)

    countries_with_poly = set(country_polygons.keys())
    countries_with_data = set(processed_data.keys())
    removed_countries = list(countries_with_poly.difference(countries_with_data))
    if show_removed:
        ax.set_xlabel("Removed countries: " + str(removed_countries) + "\n" + add_info)
    else:
        ax.set_xlabel(add_info)

    # only display the region for which we have data
    ax.set_xlim([-30, 50])
    ax.set_ylim([30, 70])

    # find maximum and minimum value to scale the colour coding
    min_val = min(processed_data.values())
    max_val = max(processed_data.values())

    # loop over all countries for which we have found a pollution and emission data. These are not necessarily the
    # same countries as the ones in the polygon dictionary, since some countries (e.g. Vatican City) are too small
    # to contain any data (the grid is too coarse). These countries will then not be plotted
    for name in processed_data:
        value = processed_data[name]  # retrieve the value for this country

        # select the colour based on the value. Nonlinear mappings can be used to make differences more apparent
        colour = plt.get_cmap(colormap)(mapping(value, min_val, max_val))
        for region in country_polygons[name][0]:  # loop over all regions that the country consists of
            ax.plot(*region.exterior.xy, alpha=0)  # plot the borders of the polygon
            ax.add_patch(PolygonPatch(region, facecolor=colour))  # fill the polygon with colour

    for name in removed_countries:
        for region in country_polygons[name][0]:  # loop over all regions that the country consists of
            ax.plot(*region.exterior.xy, alpha=0)  # plot the borders of the polygon
            ax.add_patch(PolygonPatch(region, facecolor=removed_colour))  # fill the polygon with colour

    # TODO: Add colour bar
    # gradient = mapping(np.linspace(min_val, max_val, 256), min_val, max_val)
    # gradient = np.vstack((gradient, gradient))
    # ax.imshow(gradient, aspect='auto', cmap=plt.get_cmap(colormap))


print("Creating country polygons...")
countries = create_country_polygons()
countries_with_data = countries.copy()  # the countries which can be used for analysis later on

print("Retrieving raw pollution and emission data...")
raw_data, unavailable = find_poll_em_data(countries)
for country in unavailable:
    del countries_with_data[country]

print("Processing the data...")
processed_data, removed_countries = process_data(countries, raw_data)
for country in removed_countries:
    del countries_with_data[country]

print("Performing spatial analysis...")
moran_global = morans_i_global(countries_with_data, processed_data)
geary = gearys_c(countries_with_data, processed_data)
moran_local = morans_i_local(countries_with_data, processed_data)

print("Plotting the data...")
plot(countries, processed_data, mapping=sqrt_mapping)

print("Plotting the results of the spatial analysis...")
plt.figure()
plot(countries, moran_local, add_title=" (Local Moran's I)",
     add_info="Global Moran's I: " + str(moran_global) + "\nGeary's C: " + str(geary))

print("Finished.\n")

pp = PrettyPrinter(indent=4)
print("============= RESULTS ==============\n")

print("These countries had no data available:", unavailable)
print("These countries were removed:", removed_countries)
print("Global Moran's I: ", moran_global)
print("Geary's C: ", geary)
print("Data:")
pp.pprint(processed_data)
print("Local Moran's I:")
pp.pprint(moran_local)
plt.show()
