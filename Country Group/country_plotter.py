import json
import xarray as xr

data_filename = "Aerosol.24h.JAN.OFF.nc4"
country_filename = "country_coords.txt"

with open(country_filename) as country_file:
    country_coords = json.loads(country_file.read())

DS = xr.open_dataset(data_filename)
country = "Netherlands"
coords = country_coords[country]
print(len(coords))
