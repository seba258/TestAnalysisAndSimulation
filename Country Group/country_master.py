import cartopy.io.shapereader as shpreader
from shapely import geometry
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from descartes import PolygonPatch

# the countries that are (partially) in the area for which we have data
# TODO: Calculate the area of each country within the data region to allow for area-normalised data (i.e. per sq. m)
# TODO: Plot ratio in higher resolution than just country level
# Always keep in mind that the data for countries such as Russia and Algeria are only representative of the part of that
# country which lies within the data region (and not of the entire country)
# Also note that the pollution data is influenced by areas outside of the data region (e.g. emissions from the US
# reach Western Europe and cause pollution), while emission data is only from above Europe
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

poll_on_filename = "Soot.24h.JAN.ON.nc4"  # NetCDF file containing pollution with aircraft on
poll_off_filename = "Soot.24h.JAN.OFF.nc4"  # NetCDF file containing pollution with aircraft off
em_filename = "AvEmMasses.nc4"  # NetCDF file containing aircraft emissions


# create a dictionary containing the polygons for all countries listed in "interesting". This function returns a
# dictionary with the format "country_name: [list of polygons that it is made up of]"
def create_country_polygons():
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
            country_dict[country_name] = []  # create empty list which will be filled with the polygons of the country
            multipolygon = country.geometry.geoms  # a multipolygon can consist of several disjoint polygons
            for polygon in multipolygon:  # each of these is a shapely polygon
                country_dict[country_name].append(polygon)

    return country_dict


# find the name of the country in which the coordinates (lon, lat) lie. Return None if it does not lie inside any
# of the countries listed in "countries". "countries" has the same format as the return value of
# create_country_polygons(), i.e. a dictionary with country names as keys and lists of polygons as values
def find_country_name(countries, lon, lat):
    for name in countries:  # loop over all countries
        for region in countries[name]:  # loop over each polygon that the country is made of
            if region.contains(geometry.Point(lon, lat)):  # check if the polygon contains the coordinates
                return name
    return None


# find the ground level pollution (BC due to aircraft) to aircraft BC emission ratio for each country, and return it
# in a dictionary.
def find_poll_em_ratios(countries):
    DS = xr.open_dataset(em_filename)
    da_em = DS.BC  # select only the BC (black carbon) emissions since it is inert

    DS_on = xr.open_dataset(poll_on_filename)
    DS_off = xr.open_dataset(poll_off_filename)

    # subtract pollution data without aircraft from pollution with aircraft to retrieve the pollution caused by
    # aircraft only. Also, only select BC
    da_poll = DS_on.AerMassBC - DS_off.AerMassBC

    # find the number of time steps in the data, to allow for time averaging of the pollution data
    t_steps = len(da_poll.coords['time'].values)

    poll_em_ratios = {}
    lon_axis = da_em.coords['lon'].values  # the longitude values of the data grid
    lat_axis = da_em.coords['lat'].values  # the latitude values of the data grid

    # this block fills poll_em_ratios in the format "country_name: [total_emissions, time_averaged_pollution]"
    for lon in lon_axis:
        for lat in lat_axis:  # loop over all cells in the data grid
            country = find_country_name(countries, lon, lat)  # find the country the cell lies in
            if country is not None:
                if country not in poll_em_ratios:
                    # if this is the first time the country is detected, set emission and pollution counters to 0
                    poll_em_ratios[country] = [0, 0]
                # select the correct values from the simulation data and add it to the counters. Sum over all parameters
                # which are not explicitly specified (e.g. time or altitude)
                poll_em_ratios[country][0] += np.sum(da_em.sel(lon=lon, lat=lat).values)
                poll_em_ratios[country][1] += np.sum(da_poll.sel(lon=lon, lat=lat)
                                                     .sel(lev=1, method='nearest').values) / t_steps

    # calculate the ratios from the data found in the previous block to get the format "country_name: ratio"
    for country in poll_em_ratios:
        poll_em_ratios[country] = poll_em_ratios[country][1] / poll_em_ratios[country][0]

    return poll_em_ratios


# show map with colour coding for the pollution over emission ratios
def plot(countries, poll_em_ratios):
    ax = plt.gca()  # get the axes of the current figure
    ax.set_title("Relative Pollution/Emission Ratio in January")

    # only display the region for which we have data
    ax.set_xlim([-30, 50])
    ax.set_ylim([28, 72])

    # find maximum and minimum ratio to scale the colour coding
    min_ratio = min(poll_em_ratios.values())
    max_ratio = max(poll_em_ratios.values())

    # loop over all countries for which we have found a pollution over emission ratio. These are not necessarily the
    # same countries as the ones in the polygon dictionary, since some countries (e.g. Vatican City) are too small
    # to contain any data (the grid is too coarse). These countries will then not be plotted
    for name in poll_em_ratios:
        value = poll_em_ratios[name]  # retrieve the ratio for this country

        # select the colour based on the value. Darker colours mean a higher ratio, i.e. more ground level pollution
        # for the same amount of emissions. The mapping from value to colour is based on the square root since that
        # makes the differences more obvious than a linear mapping
        colour = 1 - np.sqrt((value - min_ratio) / (max_ratio - min_ratio))
        for region in countries[name]:  # loop over all regions that the country consists of
            ax.plot(*region.exterior.xy, alpha=0)  # plot the borders of the polygon
            ax.add_patch(PolygonPatch(region, facecolor=(colour, colour, colour)))  # fill the polygon with colour


print("Creating country polygons...")
countries = create_country_polygons()
print("Finding pollution to emission ratios...")
poll_em_ratios = find_poll_em_ratios(countries)
print("Plotting...")
plot(countries, poll_em_ratios)
print("Finished")
plt.show()
