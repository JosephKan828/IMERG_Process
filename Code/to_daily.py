# ====================================================
# This file is to convert half-hourly IMERG HDF5 data
# into daily netCDF4 data
# ====================================================

# ====================================================
# Import package
# ====================================================

import h5py
import numpy as np
import netCDF4 as nc


from concurrent.futures import ProcessPoolExecutor
from glob import glob
from typing import DefaultDict, List, Tuple
from pathlib import Path
from collections import defaultdict

from tqdm import tqdm


# =====================================================
# Parallel computation setup
# =====================================================

N_WORKERS: int = 8

worker_lon        : np.ndarray
worker_lat        : np.ndarray
worker_output_path: Path


def initialize_worker(
    lon: np.ndarray,
    lat: np.ndarray,
    output_path: Path,
) -> None:

    global worker_lon, worker_lat, worker_output_path

    worker_lon         = lon
    worker_lat         = lat
    worker_output_path = output_path


# =====================================================
# Convert one day
# =====================================================

def process_date(
    Task: Tuple[str, List[str]],
) -> Tuple[str, int, bool]:

    Date, Daily_Files = Task
    year, month, day = Date[:4], Date[4:6], Date[6:8]

    # Skip a date that has already been converted. This allows the script to
    # continue from the previous stopping point when it is run again.
    saving_path: Path = worker_output_path / year / month
    output_file: Path = saving_path / f"{day}.nc"

    if output_file.exists():
        return Date, len(Daily_Files), True

    prec_daily: np.ndarray = np.zeros(
        (worker_lat.size, worker_lon.size), dtype=np.float32
    )
    valid_count: np.ndarray = np.zeros(
        (worker_lat.size, worker_lon.size), dtype=np.uint8
    )

    # Each worker reads one file at a time to avoid storing all 48 global
    # precipitation fields in memory at the same time.
    for File in Daily_Files:

        with h5py.File(File, "r") as ds:

            prec_ds = ds["Grid/precipitation"]

            if not isinstance(prec_ds, h5py.Dataset):
                raise TypeError(
                    "The HDF5 object at '/Grid/precipitation' is not a dataset"
                )

            prec: np.ndarray = np.asarray(prec_ds[...]).squeeze().T

        # IMERG precipitation is in mm/hr. Each file covers 0.5 hour.
        # NumPy writes directly into the existing arrays to avoid temporary
        # arrays created by Boolean indexing.
        valid: np.ndarray = prec > -9000
        np.multiply(prec, 0.5, out=prec, where=valid)
        np.add(prec_daily, prec, out=prec_daily, where=valid)
        np.add(valid_count, 1, out=valid_count, where=valid)

    prec_daily[valid_count == 0] = np.nan

    # -------------------------------------------------
    # Write daily netCDF4 file
    # -------------------------------------------------

    saving_path.mkdir(parents=True, exist_ok=True)

    with nc.Dataset(output_file, "w", format="NETCDF4") as ds:

        ds.createDimension("lat", worker_lat.size)
        ds.createDimension("lon", worker_lon.size)

        lat_nc  = ds.createVariable("lat", "f4", ("lat",))
        lon_nc  = ds.createVariable("lon", "f4", ("lon",))
        prec_nc = ds.createVariable(
            "precipitation",
            "f4",
            ("lat", "lon"),
            fill_value=-9999.0,
        )

        lat_nc.units  = "degrees_north"
        lon_nc.units  = "degrees_east"
        prec_nc.units = "mm/day"

        lat_nc[:]     = worker_lat
        lon_nc[:]     = worker_lon
        prec_nc[:, :] = np.ma.masked_invalid(prec_daily)

    return Date, len(Daily_Files), False


# =====================================================
# Main function
# =====================================================

def main() -> None:

    # -------------------------------------------------
    # Path setup
    # -------------------------------------------------

    data_path  : Path = Path("/work/DATA/Satellite/IMERG_HDF5")
    output_path: Path = Path("/data92/b11209013/IMERG/DATA")

    output_path.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # Collect files and dates
    # -------------------------------------------------

    Files: List[str] = sorted(glob(str(data_path / "*.HDF5")))

    if len(Files) == 0:
        raise FileNotFoundError(f"No HDF5 files were found in {data_path}")

    # Group the files by date in one pass. This avoids searching through all
    # archive files again for every date in the daily conversion loop.
    Files_by_Date: DefaultDict[str, List[str]] = defaultdict(list)

    for File in Files:

        Date: str = Path(File).name.split(".")[4].split("-")[0]
        Files_by_Date[Date].append(File)

    Dates: List[str] = sorted(Files_by_Date)

    # -------------------------------------------------
    # Load longitude and latitude
    # -------------------------------------------------

    with h5py.File(Files[0], "r") as ds:

        lon_ds = ds["Grid/lon"]
        lat_ds = ds["Grid/lat"]

        if not isinstance(lon_ds, h5py.Dataset):
            raise TypeError("The HDF5 object at '/Grid/lon' is not a dataset")
        if not isinstance(lat_ds, h5py.Dataset):
            raise TypeError("The HDF5 object at '/Grid/lat' is not a dataset")

        lon: np.ndarray = np.asarray(lon_ds[...]).squeeze()
        lat: np.ndarray = np.asarray(lat_ds[...]).squeeze()

    # -------------------------------------------------
    # Convert dates in parallel
    # -------------------------------------------------

    Tasks: List[Tuple[str, List[str]]] = [
        (Date, Files_by_Date[Date]) for Date in Dates
    ]

    with ProcessPoolExecutor(
        max_workers=N_WORKERS,
        initializer=initialize_worker,
        initargs=(lon, lat, output_path),
    ) as executor:

        Results = executor.map(process_date, Tasks, chunksize=1)

        for Date, File_Count, Skipped in tqdm(Results, total=len(Tasks)):

            if File_Count != 48:
                tqdm.write(
                    f"Warning: {Date} contains {File_Count} files "
                    "instead of 48 files"
                )

# =====================================================
# Execute main function
# =====================================================

if __name__ == "__main__":
    main()
