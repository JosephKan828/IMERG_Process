# ====================================================
# This file is to convert IMERG HDF5 data into netCDF4
# format
# ====================================================

# ====================================================
# Import package
# ====================================================

import h5py
import numpy as np
import netCDF4 as nc


from glob import glob
from typing import List
from pathlib import Path

from matplotlib import pyplot as plt

# =====================================================
# Main function
# =====================================================

def main() -> None:

    # -------------------------------------------------
    # Load data
    # -------------------------------------------------

    # path setup
    data_path: Path = Path("/work/DATA/Satellite/IMERG_HDF5")

    # collect files
    Files: List = glob(str(data_path / "*.HDF5"))

    with h5py.File(Files[0], "r") as ds:

        lon_ds  = ds["Grid/lon"]
        lat_ds  = ds["Grid/lat"]
        prec_ds = ds["Grid/precipitation"]

        if not isinstance(lon_ds, h5py.Dataset):
            raise TypeError("The HDF5 object at '/Grid/lon' is not a dataset")
        if not isinstance(lat_ds, h5py.Dataset):
                    raise TypeError("The HDF5 object at '/Grid/lat' is not a dataset")
        if not isinstance(prec_ds, h5py.Dataset):
                    raise TypeError("The HDF5 object at '/Grid/precipitation' is not a dataset")

        lon : np.ndarray = np.asarray(lon_ds[...])
        lat : np.ndarray = np.asarray(lat_ds[...])
        prec: np.ndarray = np.asarray(prec_ds[...])

    # -------------------------------------------------
    # Filter missing value
    # -------------------------------------------------

    prec_valid: np.ndarray = np.where(prec <= -9000, np.nan, prec)

    



# =====================================================
# Execute main function
# =====================================================

if __name__ == "__main__":
    main()
