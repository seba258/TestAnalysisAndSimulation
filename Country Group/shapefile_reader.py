import cartopy.io.shapereader as shpreader
from matplotlib import pyplot as plt

# data from 2016 for 1:20 million scale world map. More coarse or detailed maps are available. The coordinate system is
# with longitude and latitude in degrees
filename = 'Shapefiles/CNTR_RG_20M_2016_4326.shp'

reader = shpreader.Reader(filename)

# this is a generator, not a list. So you can only loop over it, not use indexing. But if necessary, it can be converted
# using list( ).
countries = reader.records()

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

for country in countries:
    # the .split( ) part in this statement is necessary because for some reason the names have \x00\x00\x00... added
    # to them. If you don't remove that, the statement doesn't find any of them in the "interesting" list
    if country.attributes['NAME_ENGL'].split("\x00")[0] in interesting:
        # print(country.attributes['NAME_ENGL'])
        multipolygon = country.geometry.geoms  # a multipolygon can consist of several disjoint polygons
        for polygon in multipolygon:  # each of these is a shapely polygon
            plt.plot(*polygon.exterior.xy)

    else:  # called for countries that are not "interesting"
        # print("                            ", country.attributes['NAME_ENGL'])
        pass

plt.show()
