import cartopy.io.shapereader as shpreader
from shapely import geometry
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from descartes import PolygonPatch

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

poll_on_filename = "Soot.24h.JAN.ON.nc4"
poll_off_filename = "Soot.24h.JAN.OFF.nc4"
em_filename = "AvEmMasses.nc4"


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
            country_dict[country_name] = []
            multipolygon = country.geometry.geoms  # a multipolygon can consist of several disjoint polygons
            for polygon in multipolygon:  # each of these is a shapely polygon
                country_dict[country_name].append(polygon)

    return country_dict


def find_country_name(countries, lon, lat):
    for name in countries:
        for region in countries[name]:
            if region.contains(geometry.Point(lon, lat)):
                return name
    return None


def find_poll_em_ratios(countries):
    DS = xr.open_dataset(em_filename)
    da_em = DS.BC

    DS_on = xr.open_dataset(poll_on_filename)
    DS_off = xr.open_dataset(poll_off_filename)
    da_poll = DS_on.AerMassBC - DS_off.AerMassBC
    t_steps = len(da_poll.coords['time'].values)

    poll_em_ratios = {}
    lon_axis = da_em.coords['lon'].values
    lat_axis = da_em.coords['lat'].values

    for lon in lon_axis:
        for lat in lat_axis:
            country = find_country_name(countries, lon, lat)
            if country is not None:
                if country not in poll_em_ratios:
                    poll_em_ratios[country] = [0, 0]
                poll_em_ratios[country][0] += np.sum(da_em.sel(lon=lon, lat=lat).values)
                poll_em_ratios[country][1] += np.sum(da_poll.sel(lon=lon, lat=lat)
                                                     .sel(lev=1, method='nearest').values) / t_steps

    for country in poll_em_ratios:
        poll_em_ratios[country] = poll_em_ratios[country][1] / poll_em_ratios[country][0]

    return poll_em_ratios


def plot(countries, poll_em_ratios):
    ax = plt.gca()
    ax.set_title("Relative Pollution/Emission Ratio in January")
    ax.set_xlim([-30, 50])
    ax.set_ylim([28, 72])
    min_ratio = min(poll_em_ratios.values())
    max_ratio = max(poll_em_ratios.values())
    for name in countries:
        if name in poll_em_ratios:
            value = poll_em_ratios[name]
            colour = 1 - np.sqrt((value - min_ratio) / (max_ratio - min_ratio))
            for region in countries[name]:
                ax.plot(*region.exterior.xy, alpha=0)
                ax.add_patch(PolygonPatch(region, facecolor=(colour, colour, colour)))


print("Creating country polygons...")
countries = create_country_polygons()
print("Finding pollution to emission ratios...")
poll_em_ratios = find_poll_em_ratios(countries)
print("Plotting...")
plot(countries, poll_em_ratios)
print("Finished")
plt.show()
