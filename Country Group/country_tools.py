from collections import OrderedDict
import cartopy.io.shapereader as shpreader
from shapely import geometry
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from descartes import PolygonPatch
from pyproj import Geod, Transformer
import json
import pathlib

"""
Tools to analyse emission and pollution on a country level. For more explanation how to use them, check the other files
in this directory.

@author Jakob Schoser
"""

# different modes for plotting emission and/or pollution data
PLOT_RATIO = "Ground Pollution/Emission Ratio"
PLOT_EMISSIONS = "Emissions"
PLOT_POLLUTION = "Ground Pollution"

# different ways of to combine the data inside one country
METHOD_AVG = "Area average"
METHOD_MEDIAN = "Median"


# return the name of a cache file which was created using the same settings that the program is now run on. Will be used
# to look for such a file or create one if it doesn't already exist
def cache_filename(poll_coll, summer, poll_chem, em_chem, em_lev):
    return poll_coll + "_" + ("JUL" if summer else "JAN") + "_" + poll_chem + "_" + em_chem + "_" +\
           str(em_lev.start) + "_" + str(em_lev.stop)


# return a path object leading to the data directory
def data_dir():
    return pathlib.Path.cwd().parent / "Data"


# generate the name of a data file using the convention
def data_filename(poll_coll, summer, poll_on):
    return poll_coll + ".{}.{}.nc4".format("JUL" if summer else "JAN", "ON" if poll_on else "OFF")


# create a dictionary containing the polygons for all countries listed in "interesting". This function returns an
# ordered dictionary with the format "country_name: [[list of polygons that it is made up of], total area]"
def create_country_polygons(shapefile_path="Shapefiles/CNTR_RG_20M_2016_4326.shp",
                            country_list_filename="countries.json"):
    frame = geometry.Polygon([(-30, 30), (50, 30), (50, 70), (-30, 70)])  # the geographic area for which we have data
    geod = Geod('+a=6378137 +f=0.0033528106647475126')  # object used for conversion from degrees to km

    # read the shape file
    reader = shpreader.Reader(shapefile_path)

    # this is a generator, not a list. So you can only loop over it, not use indexing. But if necessary, it can be
    # converted using list( ).
    countries = reader.records()

    # list of all countries to be checked
    country_file = json.load(open(country_list_filename))

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


# find the ground level pollution due to aircraft and aircraft emission data for each country, and return it
# in an ordered dictionary in the form "country_name: [emission, pollution]".
def find_poll_em_data(country_polygons, poll_coll, em_chemical, poll_chemical, emission_levels, summer,
                      em_filename="AvEmFluxes.nc4", data_dir=pathlib.Path.cwd().parent / "Data",
                      recalculate_country_cells=False, country_cell_filename="country_cells.json"):

    em_filepath = data_dir / em_filename
    poll_on_filepath = data_dir / data_filename(poll_coll, summer, True)
    poll_off_filepath = data_dir / data_filename(poll_coll, summer, False)

    DS = xr.open_dataset(em_filepath)
    da_em = getattr(DS, em_chemical)  # select only the specified emissions

    DS_on = xr.open_dataset(poll_on_filepath)
    DS_off = xr.open_dataset(poll_off_filepath)

    # subtract pollution data without aircraft from pollution with aircraft to retrieve the pollution caused by
    # aircraft only. Also, only select the appropriate chemical
    da_poll = getattr(DS_on, poll_chemical) - getattr(DS_off, poll_chemical)

    poll_em_data = {}
    lon_axis = da_em.coords['lon'].values  # the longitude values of the data grid
    lat_axis = da_em.coords['lat'].values  # the latitude values of the data grid

    if pathlib.Path(country_cell_filename).exists() and not recalculate_country_cells:
        country_cells = json.load(open(country_cell_filename))
        print("Retrieved list of cells per country from existing file")

    else:  # in case there is no cache file or the user wants to recalculate it
        country_cells = {}
        for lon in lon_axis:
            for lat in lat_axis:  # loop over all cells in the data grid
                country = find_country_name(country_polygons, lon, lat)  # find the country the cell lies in
                if country is not None:
                    if country not in country_cells:
                        country_cells[country] = []
                    country_cells[country].append([float(lon), float(lat)])
        with open(country_cell_filename, "w") as outfile:
            json.dump(country_cells, outfile, indent=4)

    # number of time steps in the pollution file
    n_timesteps = 1
    if "time" in da_poll.coords:
        n_timesteps = len(da_poll.coords["time"].values)

    # this block fills poll_em_data in the format "country_name: [total_emissions, time_averaged_pollution]"
    for country in country_cells:
        for cell in country_cells[country]:  # loop over all cells in the data grid
            if country not in poll_em_data:
                # if this is the first time the country is detected, set emission and pollution counters to 0
                poll_em_data[country] = [[], []]
            # select the correct values from the simulation data and add it to the lists. Sum over all parameters
            # which are not explicitly specified (i.e. time in this case). Also select correct altitudes for both
            # emission and pollution. For pollution, divide by the number of time steps to get the time average
            poll_em_data[country][0].append(np.sum(da_em.sel(lon=cell[0], lat=cell[1]).sel(lev=emission_levels).values))
            poll_em_data[country][1].append(np.sum(da_poll.sel(lon=cell[0], lat=cell[1])
                                                   .sel(lev=1, method='nearest').values) / n_timesteps)

    # check for any missing countries in the file
    requested_keys = set(country_polygons.keys())
    returned_keys = set(poll_em_data.keys())
    unavailable = list(requested_keys.difference(returned_keys))

    # return data, along with the names of all missing countries
    return OrderedDict(sorted(poll_em_data.items(), key=lambda t: t[0])), unavailable


# integrate the data over the country surfaces using the chosen method, and combine emission and pollution data
# according to the selected mode. Returns an ordered dict with "country_name: value". Also returns any countries that
# were removed
def process_data(country_polygons, raw_data, method=METHOD_AVG, mode=PLOT_RATIO, outliers=None, multiplier=1):
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
            if processed_data[country][0] != 0 and (outliers is None or
                                                    not any([outlier in country for outlier in outliers])):
                # divide pollution by emissions
                processed_data[country] = processed_data[country][1] * multiplier / processed_data[country][0]
            else:  # remove the country from the data set if it is an outlier or if it has no emissions
                removed_countries.append(country)
                del processed_data[country]
    elif mode == PLOT_EMISSIONS or mode == PLOT_POLLUTION:
        for country in raw_data:
            if outliers is None or not any([outlier in country for outlier in outliers]):
                # divide pollution or emissions (depending on the mode) by the area of the corresponding country
                processed_data[country] = processed_data[country][0 if mode == PLOT_EMISSIONS else 1] * multiplier / \
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


def generate_sub_title(poll_chemical, em_chemical, summer, emission_levels, method, mode=PLOT_RATIO):
    chemical_decription = ("Pollution chemical: " + poll_chemical + " | ")\
        if mode == PLOT_RATIO or mode == PLOT_POLLUTION else ""
    chemical_decription += ("Emission chemical: " + em_chemical + " | ")\
        if mode == PLOT_RATIO or mode == PLOT_EMISSIONS else ""
    return chemical_decription + "Time frame for pollution: " + ("July" if summer else "January") +\
           " 2005 | Altitude levels for emission: " + str(emission_levels.start) + " to " + \
           str(emission_levels.stop) + " | Averaging method: " + method


# show map with colour coding for the pollution and/or emission data
def plot_map(country_polygons, processed_data, mode, poll_chemical, em_chemical, summer, emission_levels, method,
             add_title="", add_info="", show_removed=False, mapping=lin_mapping, colormap="coolwarm",
             removed_color=(0, 0, 0, 1)):
    ax = plt.gca()  # get the axes of the current figure
    ax.set_title(mode + add_title + "\n\n" +
                 generate_sub_title(poll_chemical, em_chemical, summer, emission_levels, method, mode))

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
            ax.add_patch(PolygonPatch(region, facecolor=removed_color))  # fill the polygon with colour

    # TODO: Add colour bar
    # gradient = mapping(np.linspace(min_val, max_val, 256), min_val, max_val)
    # gradient = np.vstack((gradient, gradient))
    # ax.imshow(gradient, aspect='auto', cmap=plt.get_cmap(colormap))