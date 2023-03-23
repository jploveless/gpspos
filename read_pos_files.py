import os
import numpy as np
import pandas as pd
import h5py
from datetime import datetime
from datetime import date
import re

# Check main directory
maindir = "./f5"
yeardirs = [
    x for x in os.listdir(maindir) if os.path.isdir(os.path.join(maindir, x))
]  # List of annual directories
yeardirs = np.sort(yeardirs)

# Set up blank arrays
ndates = (date.today() - date(int(yeardirs[0]), 1, 1)).days
fulldates = pd.date_range(date(int(yeardirs[0]), 1, 1), date.today())

stanames = []  # To hold unique station names
allyeardirs = []  # To hold repeated year directory names
allposfiles = []  # To hold .pos filenames

# Loops through years
for i in range(len(yeardirs)):
    # Get list of .pos files
    posfiles = [
        x for x in os.listdir(os.path.join(maindir, yeardirs[i])) if (x[-3:] == "pos")
    ]
    allyeardirs = allyeardirs + [yeardirs[i]] * len(posfiles)
    allposfiles = allposfiles + posfiles
    # Extract station names from .pos filenames
    staname = [x[0:-7] for x in posfiles]
    stanames = list(set(stanames + staname))
    stanames.sort()

nsta = len(stanames)
# Blank position arrays
X = np.zeros([nsta, ndates + 1])
Y = np.zeros([nsta, ndates + 1])
Z = np.zeros([nsta, ndates + 1])
lat = np.zeros([nsta, ndates + 1])
lon = np.zeros([nsta, ndates + 1])
hgt = np.zeros([nsta, ndates + 1])

# Read in each .pos file
for i in range(len(allposfiles)):
    df = pd.read_csv(
        os.path.join(maindir, allyeardirs[i], allposfiles[i]),
        skiprows=20,
        skipfooter=2,
        engine="python",
        sep="\s+",
        names=["year", "month", "day", "t", "x", "y", "z", "lat", "lon", "hgt"],
    )
    # Assemble date columns into datetime
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])

    # Insert positions into proper row, column
    rowid = stanames.index(allposfiles[i][0:-7])  # Row index
    colid = np.flatnonzero(
        np.in1d(fulldates, df.date) & np.in1d(fulldates, df.date)
    )  # Column indices
    X[rowid, colid] = df.x
    Y[rowid, colid] = df.y
    Z[rowid, colid] = df.z
    lon[rowid, colid] = df.lon
    lat[rowid, colid] = df.lat
    hgt[rowid, colid] = df.hgt

# Trim any blank columns
xsum = np.sum(X, axis=0)
keepcols = xsum != 0
X = X[:, keepcols]
Y = Y[:, keepcols]
Z = Z[:, keepcols]
lon = lon[:, keepcols]
lat = lat[:, keepcols]
hgt = hgt[:, keepcols]
fulldates = fulldates[keepcols]
# Convert dates to numpy array. Seems needed to save to HDF5
dates = np.array(fulldates)

# Write to HDF5 file
hf = h5py.File("geonet_f5.h5", "w")
hf["X"] = X
hf["Y"] = Y
hf["Z"] = Z
hf["lon"] = lon
hf["lat"] = lat
hf["hgt"] = hgt
hf["date"] = dates.astype(h5py.opaque_dtype(dates.dtype))
hf["name"] = stanames
hf.close()
