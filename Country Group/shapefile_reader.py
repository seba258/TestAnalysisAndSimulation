import cartopy.io.shapereader as shpreader
# from matplotlib import pyplot as plt
from shapely import geometry

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

# data from 2016 for 1:20 million scale world map. More coarse or detailed maps are available. The coordinate system is
# with longitude and latitude in degrees
filename = 'Shapefiles/CNTR_RG_20M_2016_4326.shp'
country_dict = {}


def in_country(name, coords):
    if name not in country_dict:
        return False

    for region in country_dict[name]:
        if region.contains(geometry.Point(coords)):
            return True

    return False


reader = shpreader.Reader(filename)

# this is a generator, not a list. So you can only loop over it, not use indexing. But if necessary, it can be converted
# using list( ).
countries = reader.records()

for country in countries:
    # the .split( ) part in this statement is necessary because for some reason the names have \x00\x00\x00... added
    # to them. If you don't remove that, the statement doesn't find any of them in the "interesting" list
    country_name = country.attributes['NAME_ENGL'].split("\x00")[0]
    if country_name in interesting:
        # print(country.attributes['NAME_ENGL'])
        country_dict[country_name] = []
        multipolygon = country.geometry.geoms  # a multipolygon can consist of several disjoint polygons
        for polygon in multipolygon:  # each of these is a shapely polygon
            country_dict[country_name].append(polygon)
            # plt.plot(*polygon.exterior.xy)

    else:  # called for countries that are not "interesting"
        # print("                            ", country.attributes['NAME_ENGL'])
        pass

print(in_country("Netherlands", (4.4, 52)))

# plt.show()
