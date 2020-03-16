import cartopy.crs as ccrs
from matplotlib import pyplot as plt, animation
from Altitude_converter import Altitude_Conversion
from GUI import Select_pollutant




# Check if there are different altitude levels
if hasattr(var, 'lev') and (DS.lev.max() != DS.lev.min()):
    
    # Ask for altitude in kilometers
    alt = int(input("Select altitude (km): "))
    level = Altitude_Conversion(alt)[1]
    
    da = getattr(var,"sel")(lev = level, method = 'nearest')

else:
    da = var

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
cax = da[0,:,:].plot(add_colorbar=True,
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