# https://ecocast.arc.nasa.gov/data/pub/gimms/3g.v0/
from osgeo import gdal, ogr, osr, gdalconst
import glob
import fnmatch
import os
import numpy
import subprocess
inDir='E:/tmp/download_JB'
selectRule='*.SM.nc'
outDir='E:/tmp/exportJB/'

# decode data from ftp://ftp.star.nesdis.noaa.gov/pub/corp/scsb/wguo/data/VHP_4km/VH/
# Note here we provide 7-day composite NDVI data, which is timely smoothed, with the label "SM" in the file name. And if you download the data, you can access it using the variable name "SMN".
# If you need NDVI data without time smoothing, we provide coarse resolution data at
# ftp://ftp.star.nesdis.noaa.gov/pub/corp/scsb/wguo/data/VHP_16km/VH/
# Here you can find also 7-day composite NDVI data, only the resolution is 16 km. The un-smoothed NDVI data have the label "ND" in the file name.

ulx=-180
lrx=180
uly=75.024002
lry=-55.152
ncols=10000
nlines=3616
psx=int((lrx-ulx)/float(ncols))
psy=int((uly-lry)/float(nlines))
wulx=-11.0
wlrx=19
wlry=-5.2
wuly=3.7
format='gtiff'
options=['compress=lzw']

# ____________
# define a regular output name
def defineName(inName):

	return 'ndvi_{}_.tif'.format(inName.replace('VHP.G04.C07.NJ.P','').replace('.SM.nc',''))
# _______________________________
# main code

# get list of filenames, do sub-folder search
inFnames = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(inDir) for f in fnmatch.filter(files, selectRule)]
if not os.path.isdir(outDir):
	os.makedirs(outDir)

gt=[ulx, psx, 0, uly, 0, -psy]

# loop over list, read binary, write as image
for ii in inFnames:
	print ii
	outName = os.path.join(outDir, defineName(os.path.basename(ii)))
	#os.system('gdal_translate -of gtiff -co compress=lzw "NETCDF:{}:SMN" "{}"'.format(ii, outName))
	thisFid = gdal.Open('NETCDF:"{}":SMN'.format(ii), gdalconst.GA_ReadOnly)
	thisData = numpy.flipud(thisFid.GetRasterBand(1).ReadAsArray(0, 0, ncols, nlines))
	thisOut = gdal.GetDriverByName(format).Create(outName, ncols, nlines, 1, outputType, options=options )
	thisOut.SetProjection('EPSG:4326')
	thisOut.SetGeoTransform(gt)
	thisOut.GetRasterBand(1).WriteArray(thisData.reshape(ncols, -1))
	stop()

# end of script