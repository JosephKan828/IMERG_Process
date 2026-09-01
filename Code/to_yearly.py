# ====================================================
# This script is to concatenate daily IMERG files into yearly files.
# ====================================================

# ====================================================
# Import libraries
# ====================================================

import os

import h5py
import numpy as np
import netCDF4 as nc


from concurrent.futures import ProcessPoolExecutor
from glob import glob
from typing import DefaultDict, List, Tuple
from pathlib import Path
from collections import defaultdict

from tqdm import tqdm

# ====================================================
# Main function
# ====================================================

def main(year: float) -> None:

    # ------------------------------------------------
    # Load data
    # ------------------------------------------------

    # path setup
    root_path: Path = Path(__file__).resolve().parent.parent

    # collect files within a year
    ## direct to the directory of the year
    year_path: Path = root_path / "Data" / "IMERG" / f"{int(year)}"

    ## collect all files within the year
    daily_files: List[str] = [d for d in glob(str(year_path / "*")) if os.path.isdir(d)]

    
    print(daily_files)


# ====================================================
# Execute main function
# ====================================================

if __name__ == "__main__":

    year: float = 2006

    main(year)