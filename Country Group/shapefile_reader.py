import cartopy.io.shapereader as shpreader
from shapely import geometry
import xarray as xr
import numpy as np
import json

# from matplotlib import pyplot as plt

# the countries that are (partially) in the area for which we have data
# TODO: Calculate the area of each country within the data region, and export is as well so the data can be normalised
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
    "Svalbard and Jan Mayen"
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

print("Preparing...")

# data from 2016 for 1:20 million scale world map. More coarse or detailed maps are available. The coordinate system is
# with longitude and latitude in degrees
shape_file = 'Shapefiles/CNTR_RG_20M_2016_4326.shp'

# this file is used to get the grid points on which we have the data
data_file = 'Aerosol.24h.JAN.OFF.nc4'

# the keys are country names (in English), and the value for each of them is a list with the polygons that the country
# shape is made up of
country_dict = {}


# this function checks if country_dict contains a country with the given name. If so, it returns whether this country
# contains the given coordinates (longitude, latitude)
def in_country(name, coords):
    if name not in country_dict:
        return False

    for region in country_dict[name]:
        if region.contains(geometry.Point(coords)):
            return True

    return False


# read the shape file
reader = shpreader.Reader(shape_file)

# this is a generator, not a list. So you can only loop over it, not use indexing. But if necessary, it can be converted
# using list( ).
countries = reader.records()

# get the values of longitude and latitude at which the grid points lie
DS = xr.open_dataset(data_file)
lon_values = DS.coords['lon'].values
lat_values = DS.coords['lat'].values

# combine longitude and latitude into a list of all grid cell coordinates in the form [lon, lat]
xx, yy = np.meshgrid(lon_values, lat_values)
grid_cells = np.array((xx.ravel(), yy.ravel())).T

print("Getting country shapes...")

# fill the country_dict
for country in countries:
    # the .split( ) part in this statement is necessary because for some reason the names have \x00\x00\x00... added
    # to them. If you don't remove that, the statement doesn't find any of them in the "interesting" list
    country_name = country.attributes['NAME_ENGL'].split("\x00")[0]
    if country_name in interesting:
        country_dict[country_name] = []
        multipolygon = country.geometry.geoms  # a multipolygon can consist of several disjoint polygons
        for polygon in multipolygon:  # each of these is a shapely polygon
            country_dict[country_name].append(polygon)

print("Assigning grid cells to countries...")

# the keys are country names (in English), and the value for each of them is a list with the grid points that lie inside
country_coords = {}

# loop over all countries and grid cells to fill the country_coords
for country in country_dict:
    country_coords[country] = []
    for cell in grid_cells:
        if in_country(country, cell):
            country_coords[country].append(cell.tolist())

print("Writing result to output file...")

# write the output to a file so that it can be used in other programs (if there already is a file with this name, it
# will be overwritten). The file format used is JSON (very similar to dict)
with open("country_coords.txt", "w") as output_file:
    output_file.write(json.dumps(country_coords, sort_keys=True, indent=4, separators=(',', ': ')))

print("Finished")
