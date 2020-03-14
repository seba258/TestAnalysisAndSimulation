from tkinter import filedialog
import tkinter as tk
from tkinter.ttk import *
import xarray as xr
from tkinter import messagebox

def Select_pollutant():
    def open_file():

        # Make filepath global variable, so it gets returned outside the button function
        global filepath

        # Open filedialog window
        filepath = filedialog.askopenfilename(
            filetypes=(("netCDF files", "*.nc4"), ("all files", "*.*")))

        # Extract data set from netCFD file
        DS = xr.open_dataset(filepath)

        # Make list with variables
        varlst = []
        for i in DS.variables:
            if i not in ['lev', 'lon', 'lat', 'ilev', 'time']:
                varlst.append(i)

        options = varlst

        # Create tkinter variable
        tkvar = tk.StringVar(window)

        # Instructions for dropdown
        label = tk.Label(window, text="Choose Pollutant:")
        label.grid(column=0, row=1)

        # Create dropdown menu
        dropdown = tk.OptionMenu(window, tkvar, *options)
        dropdown.grid(column = 1,row = 1)

        # Get value of dropdown
        def dropdown_val(*args):
            global val
            val = str(tkvar.get())

        # Store value of dropdown
        tkvar.trace('w', dropdown_val)

    # Initialize window
    window = tk.Tk()

    # Set title
    window.title("Select Dataset")


    # Create tkinter variable
    tkvar = tk.StringVar(window)

    # button to open file dialog
    b1 = tk.Button(window, text=" Open File ", command=open_file)
    b1.grid(column=0, row=0)



    # button to confirm selection
    btn_ok = tk.Button(window, text="   OK   ", command=window.destroy)
    btn_ok.grid(column=1, row=2)

    def cancel():
        window.destroy()
        quit()
    # Cancel and stop program
    btn_cancel = tk.Button(window, text = "    cancel    ", command = cancel)
    btn_cancel.grid(column = 0, row = 2)

    # Run window loop
    window.mainloop()

    try:

        return val
    except:
        messagebox.showinfo('Error', 'No pollutant selected')
        quit()

print(Select_pollutant())


