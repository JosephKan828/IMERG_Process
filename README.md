# IMERG_Process

## Procedure

The `Code/to_daily.py` script converts half-hourly IMERG precipitation data
from HDF5 format into daily netCDF4 files.

1. Collect all IMERG HDF5 files from
   `/work/DATA/Satellite/IMERG_HDF5`.
2. Extract the date from each filename and group the 48 half-hourly files
   belonging to the same date.
3. Read `Grid/precipitation` from each file and remove missing values smaller
   than or equal to `-9000` (The exact missing value is `-9999.0`).
4. Convert precipitation from `mm/hr` to the half-hourly accumulation and sum
   it over the day:

   ```text
   daily precipitation = sum(half-hourly precipitation * 0.5 hour)
   ```

5. Process multiple dates in parallel. The number of processes is controlled
   by `N_WORKERS` in `Code/to_daily.py`.
6. Save each daily field in `mm/day` using the following directory structure:

   ```text
   DATA/YYYY/MM/DD.nc
   ```

The script reports dates that do not contain 48 files and skips daily output
files that already exist, allowing an interrupted conversion to continue.

Run the conversion from the project directory with:

```bash
python Code/to_daily.py
```

## Logging

- 2026/08/31: Finished the test loading (file: `Code/test.py`)
- 2026/09/01:
  - Change name `Code/test.py` to `Code/to_daily.py`
  - Finish `Code/to_daily`, run in the background
  - Move concatenated data to `/work/DATA/Satellite/IMERG_daily/v20260901/`
