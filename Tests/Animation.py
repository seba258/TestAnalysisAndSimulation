import numpy as np
import xarray as xr
import cartopy.crs as ccrs
from Altitude_converter import Altitude_Conversion
from matplotlib import pyplot as plt, animation
import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename


def open_file():
    """Open a file for editing."""
    filepath = askopenfilename(
        filetypes=[("Text Files", "*.nc4"), ("All Files", "*.*")])
    
    
    return filepath


filepath = open_file()


# Open data
filename    = "Data/aerosol.24h.JAN.ON.nc4"

DS = xr.open_dataset(filepath)  # extract data set from netCFD file

# ---------------------------------- Selecting variables ----------------------------------------------
varlst = []
datlst = []

print("")
print("Select the variable to animate: ")
print("")
n = 0
for i in DS.variables:
    datlst.append(i)
    # Filter out different pollutions
    if i not in  ['lev','lon','lat', 'ilev', 'time']:
        
        print("Press "+ str(n) + " to select "+ i)
        varlst.append(i)
        
        n +=1
        
select = int(input("Selection: "))

var = getattr(DS, varlst[select])


# Check if there are different altitude levels
if DS.lev.max() != DS.lev.min():
    
    # Ask for altitude in kilometers
    alt = int(input("Select altitude (km): "))
    level = Altitude_Conversion(alt)[1]
    
    da = getattr(getattr(DS, varlst[select]),"sel")(lev=level, method='nearest')

else:
    da = getattr(DS,varlst[select])

# select projection. Only seems to work with PlateCarree though
proj = ccrs.PlateCarree()  



# Determine number of points in time
n = da.time.size

# Create subplot
fig, ax = plt.subplots(figsize=(12,6))


# Create axes and add map
ax = plt.axes(projection=proj)  # create axes
ax.coastlines(resolution='50m')  # draw coastlines with given resolution

# Set color and scale of plot
cax = da[0,:,:].plot_map(add_colorbar=True,
                         cmap = 'coolwarm',
                         vmin = da.values.min(),
                         vmax = da.values.max(),
                         cbar_kwargs = {'extend':'neither'})

# Animation function
def animate(frame):
    cax.set_array(da[frame,:,:].values.flatten())
    ax.set_title("Time = " + 
                 str(da.coords["time"].values[frame])[:13])

# Animate plots
ani = animation.FuncAnimation(fig, animate, 
                              frames=n, 
                              interval = 100)
# Show plot
plt.show()