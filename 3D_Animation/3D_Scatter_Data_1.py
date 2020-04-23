import matplotlib.animation as animation
import cartopy.io.shapereader as shpreader
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

nfr = 21  # Number of frames
fps = 5  # Frame per sec



# ----------------------- Obtaining country shapes and plotting (Based on Jacob's code in country group) -------------------------------------------

summer = False  # used to select between pollution data for January and July

# the altitude levels over which emissions will be considered. Check Altitude_levels.txt for conversion to km
emission_levels = slice(1, 14)

# the ratio for these countries will be set to zero. That is useful if some countries have such high or low ratios that
# they make it impossible to see any differences between the other countries
outlier_countries = ["Iraq", "Israel", "Latvia"]

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

# show map with colour coding for the pollution over emission ratios
def plot(countries, ax):

    # Iterate through all the countries
    for name in countries:

        # Select first row of country regions (Countries have different regions, but plotting only the first row gives the borders)
        region = countries[name][0]

        # Convert POLYGON data to numpy arrays
        points = np.array(region.exterior.coords.xy).T

        # Get number of datapoints
        N = len(points)

        # Make a new array to accomodate z-coordinates
        country_points = np.zeros((N,3))

        # Add 2D coordinates to the 3D array
        country_points[:,:2] = points

        # Delete coordinates of the countries that are outside the simulation grid
        country_points = country_points[(country_points[:,0] < 50) & (country_points[:,0] > -30) & (country_points[:,1] > 30) & (country_points[:,1] < 70)]

        # Select columns for every coordinate
        lon, lat, lev = country_points[:,0], country_points[:,1], country_points[:,2]

        # Plot the countries
        ax.plot_map(lon, lat, lev, color ='black')


# Convert eta levels to altitude
def eta_to_altitude_arr(eta_array):
    # data
    alt_dat = np.genfromtxt("Altitude_levels.txt", skip_header=3, usecols=(1, 2))

    # Grid points
    grid = alt_dat[:, 0]

    # Function values at grid points
    func = alt_dat[:, 1]
    return np.interp(eta_array, grid, func)


def Datapoints():
    # Path to datafiles
    file_on = "Soot.24h.JUL.ON.nc4"
    file_off = "Soot.24h.JUL.OFF.nc4"

    # Open datafile to acces timesteps
    DS = xr.open_dataset("Soot.24h.JUL.ON.nc4").AerMassBC

    xs = []
    ys = []
    zs = []

    for time in range(DS.time.size):
        # Open datafile and select set
        DS_ON = xr.open_dataset(file_on).AerMassBC.sel(time=DS.time.values[time])

        DS_OFF = xr.open_dataset(file_off).AerMassBC.sel(time=DS.time.values[time])

        # Filtering out non-aviation data
        da = DS_ON - DS_OFF

        # Threshold
        thrs = float(da.mean()) * 10  # 15X mean gives cruise level pollution, but slow

        # Store indices of location where pollution exceeds threshold
        sel = np.argwhere(np.array(da) > thrs)

        # Convert indices to coordinates
        lev = np.take(da.lev.values, sel[:, 0])
        lat = np.take(da.lat.values, sel[:, 1])
        lon = np.take(da.lon.values, sel[:, 2])

        # Change array type to float
        sel = sel.astype('float64')

        # Add coordinates to array
        sel[:, 0] = eta_to_altitude_arr(lev)
        sel[:, 1] = lat
        sel[:, 2] = lon


        # Make lists containing arrays with coordinates for 1 day
        xs.append(lon)
        ys.append(lat)
        zs.append(eta_to_altitude_arr(lev))

    return xs, ys, zs


# Retrieve datapoints
xs, ys, zs = Datapoints()

# Make figure and axis for plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Get the polygons for the countries
countries = create_country_polygons()

# Add the country outlines to the plot
plot(countries, ax)

sct, = ax.plot_map([], [], [], "o", markersize=2)

# Function to plot in animation
def update(ifrm, xa, ya, za):
    sct.set_data(xa[ifrm], ya[ifrm])
    sct.set_3d_properties(za[ifrm])




# Set axis limits
ax.set_xlim(-30, 50)
ax.set_ylim(30, 70)
ax.set_zlim(0, 15)

# Set axis Titles
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_zlabel("Altitude")
ax.set_title("3D Animation")

# Animation
ani = animation.FuncAnimation(fig, update, nfr, fargs=(xs, ys, zs), interval=1000 / fps)
plt.show()

