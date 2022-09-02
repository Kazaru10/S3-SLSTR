import os
from osgeo import gdal
from netCDF4 import Dataset 
import numpy as np
from qgis.core import (
    QgsRasterLayer,
    QgsProject,
    QgsPointXY,
    QgsRaster,
)

## importation et egalisation data LST
path2S3prod = r"path2prod"

subdir = os.listdir(path2S3prod)

path2LST = path2S3prod + '\\' + subdir[0] + 'LST_in.nc'
path2geo = path2S3prod + '\\' + subdir[0] + 'geodetic_in.nc' 

LST_1 = Dataset(path2LST)
LST_2 = LST_1['LST'][:]

# Histogram stretching
LST = np.zeros(np.shape(LST_2))
LST_min = LST_2.min()
LST_max = LST_2.max()

for i in range(np.shape(LST_2)[0]):
    for j in range(np.shape(LST_2)[1]):
        LST[i,j] = LST_2[i,j]*255/(LST_max - LST_min)

del LST_2
del LST_1

## geographic coordinates management
geo_1 = Dataset(path2geo)

# lat
lat = geo_1['latitude_in'][:]

# lon
lon = geo_1['longitude_in'][:]

del geo_1

nrows,ncols = np.shape(LST)

# GCPs creation (x, y, lon, lat) 
gcps = []
for i in range(0,nrows-1,50):
    for j in range(0,ncols-1,50):
        gcps.append((j, i, lon[i,j], lat[i,j]))

gcps.append((ncols-1, nrows-1, lon[nrows-1,ncols-1], lat[nrows-1,ncols-1]))

# temporary raster creation
output = path2S3prod + '\\' + "rast_tmp.tif"

driver = gdal.GetDriverByName('GTiff')
ds_2 = driver.Create(output, ncols, nrows, 1, gdal.GDT_Float32)
ds_2.GetRasterBand(1).WriteArray(LST)

ds_2.FlushCache()
ds_2 = None
ds_3 = gdal.Open(output)

# GCPs taken into account
output = path2S3prod + '\\' + 'raster_out_georef.tif.tif'

gdal.Translate(
    output,
    ds_3,
    outputSRS='EPSG:4326',
    GCPs=[gdal.GCP(x, y, 0, pixel, line) for (pixel, line, x, y) in gcps],
)

ds_3.FlushCache()
ds_3 = None
