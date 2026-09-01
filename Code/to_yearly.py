# ====================================================
# This script is to concatenate daily IMERG files into yearly files.
# ====================================================

# ====================================================
# Import libraries
# ====================================================

import numpy as np
import netCDF4 as nc


from datetime import datetime, timedelta
from glob import glob
from typing import List
from pathlib import Path

from tqdm import tqdm

# ====================================================
# Main function
# ====================================================

def main(year: int) -> None:

    # ------------------------------------------------
    # Path setup
    # ------------------------------------------------

    root_path: Path = Path(__file__).resolve().parent.parent
    year_path: Path = root_path / "DATA" / f"{year}"
    save_path: Path = root_path / "DATA" / "yearly"

    save_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------
    # Collect daily files recursively
    # ------------------------------------------------

    daily_files: List[str] = sorted(
        glob(str(year_path / "**" / "*.nc"), recursive=True)
    )

    if len(daily_files) == 0:
        raise FileNotFoundError(
            f"No daily netCDF4 files were found in {year_path}"
        )

    # ------------------------------------------------
    # Load longitude and latitude
    # ------------------------------------------------

    with nc.Dataset(daily_files[0], "r") as ds:

        lon: np.ndarray = np.asarray(ds["lon"][:])
        lat: np.ndarray = np.asarray(ds["lat"][:])

    # ------------------------------------------------
    # Create complete daily time axis
    # ------------------------------------------------

    start_date: datetime = datetime(year, 1, 1)
    end_date  : datetime = datetime(year + 1, 1, 1)
    N_Days    : int = (end_date - start_date).days

    Dates: List[datetime] = [
        start_date + timedelta(days=Day_Index)
        for Day_Index in range(N_Days)
    ]

    # ------------------------------------------------
    # Create yearly netCDF4 file
    # ------------------------------------------------

    save_file: Path = save_path / f"{year}.nc"

    with nc.Dataset(save_file, "w", format="NETCDF4") as ds:

        ds.createDimension("time", N_Days)
        ds.createDimension("lat", lat.size)
        ds.createDimension("lon", lon.size)

        time_nc = ds.createVariable("time", "f8", ("time",))
        lat_nc  = ds.createVariable("lat", "f4", ("lat",))
        lon_nc  = ds.createVariable("lon", "f4", ("lon",))
        prec_nc = ds.createVariable(
            "precipitation",
            "f4",
            ("time", "lat", "lon"),
            fill_value=-9999.0,
            chunksizes=(1, min(180, lat.size), min(360, lon.size)),
        )

        time_nc.units    = f"days since {year}-01-01 00:00:00"
        time_nc.calendar = "standard"
        lat_nc.units     = "degrees_north"
        lon_nc.units     = "degrees_east"
        prec_nc.units    = "mm/day"

        lat_nc[:] = lat
        lon_nc[:] = lon

        # Assign every calendar day to the time coordinate. Precipitation
        # remains at the netCDF4 fill value when its daily file is unavailable.
        time_nc[:] = nc.date2num(
            Dates,
            time_nc.units,
            time_nc.calendar,
        )

        # Write one daily field at a time to avoid loading the whole year
        # into memory.
        for File in tqdm(daily_files):

            File_Path: Path = Path(File)
            month: int = int(File_Path.parent.name)
            day  : int = int(File_Path.stem)
            Date: datetime = datetime(year, month, day)

            # Assign the daily field to its zero-based day-of-year index.
            Time_Index: int = (Date - start_date).days

            with nc.Dataset(File, "r") as daily_ds:

                prec_nc[Time_Index, :, :] = daily_ds["precipitation"][:]

    print(f"Finished {year}: {save_file}")

# ====================================================
# Execute main function
# ====================================================

if __name__ == "__main__":

    for year in range(2000, 2024):
        print(f"Processing year: {year}")
        main(year)
