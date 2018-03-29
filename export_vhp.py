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

wulx=-11.0
wlrx=19
wlry=-5.2
wuly=3.7
format='gtiff'
options=['compress=lzw']

# ____________
# define a regular output name
def defineName(inName):

	return 'ndvi_{}.tif'.format(inName.replace('VHP.G04.C07.NJ.P','').replace('.SM.nc','').replace('.','_'))
# _______________________________
# main code

# get list of filenames, do sub-folder search
inFnames = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(inDir) for f in fnmatch.filter(files, selectRule)]
if not os.path.isdir(outDir):
	os.makedirs(outDir)


proj = osr.SpatialReference()
proj.ImportFromEPSG(4326)
tmpName=os.path.join(outDir, 'tmp_export_vhp.tif')

# loop over list, read binary, write as image
for ii in inFnames:
	print ii
	if os.path.exists(tmpName):
		os.remove(tmpName)
	outName = os.path.join(outDir, defineName(os.path.basename(ii)))
	#os.system('gdal_translate -of gtiff -co compress=lzw "NETCDF:{}:SMN" "{}"'.format(ii, outName))
	thisFid = gdal.Open('NETCDF:"{}":SMN'.format(ii), gdalconst.GA_ReadOnly)
	ncols = thisFid.RasterXSize
	nlines= thisFid.RasterYSize
	psx=(lrx-ulx)/float(ncols)
	psy=(uly-lry)/float(nlines)
	print  lrx, ulx, ncols
	print uly, lry, nlines
	gt=[ulx, psx, 0, uly, 0, -psy]
	print ncols, nlines, psx, psy
	print gt
	print thisFid.GetRasterBand(1).DataType
	print outName
	thisData = numpy.flipud(thisFid.GetRasterBand(1).ReadAsArray(0, 0, ncols, nlines))
	print thisData.max()
	print thisData.min()
	print thisData.mean()
	print thisData.shape
	try:
		thisOut = gdal.GetDriverByName(format).Create(tmpName, ncols, nlines, 1, thisFid.GetRasterBand(1).DataType, options=options )
		thisOut.SetProjection(proj.ToWkt())
		print proj.ToWkt()
		thisOut.SetGeoTransform(gt)
		print gt
		thisOut.GetRasterBand(1).WriteArray(thisData, 0, 0)
		thisOut = None
	except:
		print 'error'
	finally:
		thisOut = None
	try:
		thisIn = gdal.Open(tmpName, gdalconst.GA_ReadOnly)
		#outFid = gdal.GetDriverByName(format).Create(outName, ncols, nlines, 1, thisFid.GetRasterBand(1).DataType, options=options )
		print outName
		ds = gdal.Translate(outName, thisOut, format = format, options=options, projWin = [wulx, wuly, wlrx, wlry])
		ds = None
	except:
		print 'error in gdal.Translate'
	finally:
		ds = None
	stop()

# end of script