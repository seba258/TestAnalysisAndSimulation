import tkinter as tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
from Altitude_converter import Altitude_Conversion
from tkinter.filedialog import askopenfilename, asksaveasfilename


def open_file():
    """Open a file for editing."""
    filepath = askopenfilename(
        filetypes=[("Text Files", "*.nc4"), ("All Files", "*.*")])

    return filepath




filepath = open_file()



DS = xr.open_dataset(filepath)  # extract data set from netCFD file
#------------------------------------------------------------------------
root = tk.Tk()
frame = tk.Frame(root)
frame.pack()
datlst = []
varlst = []
sel = []

for i in DS.variables:
    datlst.append(i)
    # Filter out different pollutions
    if i not in  ['lev','lon','lat', 'ilev', 'time']:
        varlst.append(i)
        button = tk.Button(frame,text = i,
                       command = lambda a = i: sel.append(a))
        button.pack(side = LEFT)

OK_button = tk.Button(frame,text = "OK",
                      command = root.destroy)
OK_button.pack(side = BOTTOM)
#select = int(input("Selection: "))

root.mainloop()

substance = sel[-1]

var = getattr(DS, substance)
# ------------------------------------------
root = tkinter.Tk()
root.wm_title("Embedding in Tk")

fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))

canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)


def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)


def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


button = tkinter.Button(master=root, text="Quit", command=_quit)
button.pack(side=tkinter.BOTTOM)

tkinter.mainloop()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.