import numpy as np
from numpy.random import normal as normal
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
import matplotlib
import xarray as xr

nfr = 21  # Number of frames
fps = 10  # Frame per sec


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

sct, = ax.plot([], [], [], "o", markersize=2)


# Function to plot in animation
def update(ifrm, xa, ya, za):
    sct.set_data(xa[ifrm], ya[ifrm])
    sct.set_3d_properties(za[ifrm])


# Set axis limits
ax.set_xlim(-30, 50)
ax.set_ylim(30, 70)
ax.set_zlim(0, 15)

# Animation
ani = animation.FuncAnimation(fig, update, nfr, fargs=(xs, ys, zs), interval=1000 / fps)
plt.show()