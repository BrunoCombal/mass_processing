from osgeo import gdal, ogr, osr, gdalconst
import glob
import fnmatch
import os
import numpy

#__________________________________________________
# Edit following parameters
# Be aware that SPOT6 has more bands than SPOT 3-5
#rInDir=u'z://Processing/All_Kongo_images/Selection_Rep_of_Congo/Selection_Spot2010/Spot4_5' # raster input dir
rInDir=u'z://Processing/All_Kongo_images/Selection_Rep_of_Congo/Selection_Spot2015/Spot5'
rOutDir=u'e://tmp/clip' #clip output dir
rRejectDir=u'e://tmp/clipBad' # rejected
duplicateDir=u'e://tmp/duplicate'
selectRule=u'*.tif' # wildcard rule
shapefile=u'e://tmp/clip/clipper_2km_square.shp'
testBand = 2
testMinMax=[0, 250] # pixel fails if value <= min or value >= max
testThreshold = 50 # maximum percentage of allowed failed pixels within the clip
exportBandList = [4,3,2]
IDField="FID"
#___________________________________________________

#
# returns BBox in EPSG:4326
#
def getBBox(fname):
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(4326)
    BBox = None
    try:
        thisFid = gdal.Open(fname, gdalconst.GA_ReadOnly)
        if thisFid is None:
            return BBox
    except IOError, e:
        return BBox
    gt = thisFid.GetGeoTransform()
    ext = []
    xarr = [0, thisFid.RasterXSize]
    yarr = [0, thisFid.RasterYSize]
    thisProjection = thisFid.GetProjection()
    transformation = osr.CoordinateTransformation(osr.SpatialReference(wkt=thisProjection), outSpatialRef)
    thisFid = None
    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            aa = transformation.TransformPoint(x, y)
            ext.append([aa[0],aa[1]])
        yarr.reverse()
    return ext

#
#
#
#
def extractInfo(thisName):
	date=None
	sensor=None
	 m = re.search(r'[12][0-9][0-9][0-9]-[012][0-9]-[0123][0-9]', thisName)
	 if m:
	 	date = m.group(0)

	 s = re.search(r'OLI', thisName.upper())
	 if s:
	 	sensor = s.group(0)
	 	return date, sensor

	 s = re.search(r'S2[AB]', thisName.upper())
	 if s:
	 	sensor = s.group(0)
	 	return date, sensor

	 s = re.search(r'SPOT_[1234567]', thisName.upper())
	 if s:
	 	sensorSeries = s.group(0)
	 	return date, sensor

# 
# ds: gdal raster file handler
# test if proportion of no-data and cloud is low
#
def testValid(ds, testBand, minmax, threshold):
	nb = ds.RasterCount
	ns = ds.RasterXSize
	nl = ds.RasterYSize
	data = numpy.ravel(ds.GetRasterBand(testBand).ReadAsArray(0, 0, ns, nl))

	nbPixels = ns*nl
	nbNodata = sum( (data <= minmax[0]) + (data >= minmax[1]) )
	propNoData = nbNodata/float(nbPixels)
	if propNoData >= threshold:
		return False
	else:
		return True

# get list of files matching the regex rule
print 'Getting list of raster files to process'

# recursive search
if selectRule != u'':
	inRasterFnames = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(rInDir) for f in fnmatch.filter(files, selectRule)]
else:
	inRasterFnames = [os.path.join(dirpath, files) for dirpath, dirnames, files in os.walk(rInDir) ]

# save their bbox
print 'Getting raster files Bounding boxes'
rasterBBox = {}
for ii in inRasterFnames:
	rasterBBox[ii]=getBBox(ii)

# clip
inShp = ogr.Open(shapefile, gdalconst.GA_ReadOnly)
layer = inShp.GetLayer()

for rr in rasterBBox:
	ii = rasterBBox[rr]
	wkt = 'POLYGON(({} {}, {} {}, {} {}, {} {}, {} {}))'.format( ii[0][0], ii[0][1], ii[1][0], ii[1][1], ii[2][0], ii[2][1], ii[3][0], ii[3][1], ii[0][0], ii[0][1] )
	layer.SetSpatialFilter( ogr.CreateGeometryFromWkt(wkt) )

	if layer.GetFeatureCount() > 0:
		#tmpFile = os.path.join( rOutDir, os.path.basename(rr) )
		#shutil.copy(rr, tmpFile)
		thisRaster = gdal.Open( rr, gdalconst.GA_ReadOnly)
		thisProjection = thisRaster.GetProjection()
		shpSpatialRef = osr.SpatialReference()
		shpSpatialRef.ImportFromEPSG(4326)
		transformation = osr.CoordinateTransformation(shpSpatialRef, osr.SpatialReference(wkt=thisProjection))

		iClip = 0
		for iFeat in layer:
			thisFeat = iFeat.GetGeometryRef()
			thisRing = thisFeat.GetGeometryRef(0)
			lon = []
			lat = []
			for point in range(thisRing.GetPointCount()):
				thisLon, thisLat, z = thisRing.GetPoint(point)
				lon.append(thisLon)
				lat.append(thisLat)
			pointMin = transformation.TransformPoint(min(lon), min(lat))
			pointMax = transformation.TransformPoint(max(lon), max(lat))
	    	# see http://svn.osgeo.org/gdal/trunk/autotest/utilities/test_gdalwarp_lib.py
			#ds = gdal.Warp('', tmpFile, format = 'MEM', outputBounds = [xmin, ymin, xmax, ymax])
			try:
				ds = gdal.Translate('', rr, format = 'MEM', projWin = [pointMin[0], pointMax[1], pointMax[0], pointMin[1]])
				# test no-data
				date, sensor = extractInfo(os.path.basename(rr))
				outFileBasename = 'fid_{}_{}'.format(iFeat.GetFID(), date, sensor)
				if os.path.exists(os.path.join(rOutDir, outFileBasename)):
					outFile = os.path.join(duplicateDir, outFileBasename)
				else:
					if testValid(ds, testBand, testMinMax, testThreshold / 100.0):
						outFile = os.path.join(rOutDir, outFileBasename)
					else:
						outFile = os.path.join(rRejectDir, outFileBasename)

				gdal.Translate(outFile, ds, format='GTIFF', options=['compress=lzw', 'bigtiff=IF_SAFER'], bandList=exportBandList)

			except Exception, e:
				print 'Error for file {}, iClip {}'.format(os.path.basename(rr), iClip)
				print '{}'.format(e)
				print [pointMin[0], pointMin[1], pointMax[0], pointMax[1]]
				print thisRaster.GetGeoTransform()
			iClip += 1
			ds=None



