#!/bin/sh

allyear_data="/data92/b11209013/IMERG/DATA/IMERG_all.nc"
rmharm_data="/data92/b11209013/IMERG/DATA/IMERG_rm3harm.nc"
regrid_data="/data92/b11209013/IMERG/DATA/IMERG_1deg.nc"

# concatenate to complete data
cdo -P 8 -mergetime /work/DATA/Satellite/IMERG_daily/v20260901/*.nc ${allyear_data}

# remove first three harmonics
cdo ydaymean ${allyear_data} climatology.nc
cdo lowpass,3 climatology.nc climatology_3harmonics.nc
cdo ydaysub ${allyear_data} climatology_3harmonics.nc ${rmharm_data}

rm -rf climatology.nc climatology_3harmonics.nc

# remap to 1 degree to 1 degree
## Define grid

cat >1deggrid <<EOF
gridtype = lonlat
xsize    = 360
ysize    = 180
xfirst   = 0.5
xinc     = 1
yfirst   = -89.4
yinc     = 1
EOF

cdo -P 8 remapbil,1deggrid ${rmharm_data} ${regrid_data}
