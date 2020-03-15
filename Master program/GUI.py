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

        global DS

        # Extract data set from netCFD file
        DS = xr.open_dataset(filepath)

        global time
        time = ''

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
        #label.grid(column=0, row=1)
        label.grid(column = 0, row = 1)
        # Create dropdown menu
        dropdown = tk.OptionMenu(window, tkvar, *options)
        dropdown.grid(column = 1,row = 1)

        # Get value of dropdown
        def dropdown_val(*args):
            global filepath
            val = str(tkvar.get())
            filepath = getattr(DS, val)

        # Store value of dropdown
        tkvar.trace('w', dropdown_val)

        # create dropdown menu for time if it is a variable
        if 'time' in DS.coords:
            options_t = DS.coords['time'].values

            # Create tkinter variable
            tkvar_t = tk.StringVar(window)

            # Instructions for dropdown
            label_t = tk.Label(window, text="Choose Time:")
            label_t.grid(column=0, row=2)
            # Create dropdown menu
            dropdown_t = tk.OptionMenu(window, tkvar_t, *options_t)
            dropdown_t.grid(column=1, row=2)

            # Get value of dropdown
            def dropdown_val_t(*args):
                global time
                time = str(tkvar_t.get())

            # Store value of dropdown
            tkvar_t.trace('w', dropdown_val_t)

        # create text field for altitude
        if 'lev' in DS.coords:
            print(DS.coords['lev'].values)

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

    btn_ok.grid(column = 1, row = 3)

    def cancel():
        window.destroy()
        quit()
    # Cancel and stop program
    btn_cancel = tk.Button(window, text = "    Cancel    ", command = cancel)
    btn_cancel.grid(column = 0, row = 3)

    # Run window loop
    window.mainloop()

    try:

        return filepath, DS, time
    except:
        messagebox.showinfo('Error', 'No pollutant selected')
        quit()



