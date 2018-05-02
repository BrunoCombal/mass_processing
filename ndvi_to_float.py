from osgeo import gdal, ogr, osr, gdalconst
import glob
import os

indir='E:/tmp/exportJB'
outdir='E:/tmp/exportJBFloat/'

scale_factor=0.001
offset=0
nodata=-999
nodataOut=-999

# get list of files
lstFiles = glob.glob('{}/ndvi_*.tif'.format(indir))

for thisFilepath in lstFiles:
	print 'Processing {}'.format(thisFilepath)
	thisFile=os.path.basename(thisFilepath)
	newFile=thisFile.replace('.tif','_float.tif')
	outFile = os.path.join(outdir, newFile)
	print outFile

	thisFid = gdal.Open(thisFilepath, gdalconst.GA_ReadOnly)
	ns = thisFid.RasterXSize
	nl = thisFid.RasterYSize
	thisData = thisFid.GetRasterBand(1).ReadAsArray(0,0,ns,nl)
	wnodata = thisData==nodata
	thisData = thisData * scale_factor + offset
	if wnodata.any():
		thisData[wnodata] = nodataOut

	# create output
	fidOut = gdal.GetDriverByName('gtiff').Create(outFile, ns, nl, 1, gdalconst.GDT_Float32, options=['compress=lzw'] )
	#print 'Output: {} {}'.format(outFile, fidOut)
	fidOut.SetProjection(thisFid.GetProjection())
	fidOut.SetGeoTransform(thisFid.GetGeoTransform())
	fidOut.GetRasterBand(1).WriteArray(thisData, 0 , 0)

	fidOut = None
	thisFile=None
