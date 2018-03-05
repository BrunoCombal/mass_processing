from osgeo import gdal, ogr, osr, gdalconst
import glob
import fnmatch
import os
import numpy
import re

#__________________________________________________
# Edit following parameters
# Be careful to change all parameters related to the specific sensor
# Be aware that SPOT6 has more bands than SPOT 3-5

#Input directory - with the images to clip
rInDir=u'Z://Processing/All_Kongo_images/Selection_Rep_of_Congo/Selection_Spot2015/Spot5_norm' # raster input dir
#rInDir=u'Y://Processing/All_Kongo_images/Selection_Rep_of_Congo/Selection_Spot2015/Spot5_norm'
#rInDir=u'Y://Processing/All_Kongo_images/Selection_Rep_of_Congo/Selection_Landsat_2014/processed2014'
#rInDir=u'P://Kongo_sentinel2_processed'

#Output directory - create 3 folders to store the good, bad and duplicate clips
rOutDir=u'e://tmp/clip' #clip output dir
rRejectDir=u'e://tmp/clipBad/' # rejected
duplicateDir=u'e://tmp/duplicate/'

#select rule of the images to clip in the input directory
selectRule=u'*21*.tif' # wildcard rule

#shapefile to clip the images
shapefile=u'E:/tmp/clip/clipper_2km_square.shp'
#u'E://verheas/ReCaREDD/WorkingData/1_RecaREDD_project/Brazza_2018/sampling/sampling_F-NF/CE_2018-03-01_F-NF/shpfile_CE_2018-03-01_F-NF-box.shp'

#band on which the test for clouds and no data is done
testBand = 2 #SPOT 4 or 5
#testBand = 3 # Landsat et sentinel

#values for cloud masking
testMinMax=[0, 248] # pixel fails if value <= min or value >= max SPOT4 or 5
#testMinMax=[0, 50] # pixel fails if value <= min or value >= max Landsat
#testMinMax=[0, 1850] # pixel fails if value <= min or value >= max S2

#threshold allowed for failed pixels within the clip
testThreshold = 20 # maximum percentage of allowed failed pixels within the clip
#testThreshold = 10 # lower the percentage for Sentinel 2 maximum percentage of allowed failed pixels within the clip

#Bands to export in the clip
exportBandList = [4,1,2] #SPOT4 or 5
#exportBandList = [5,4,3] # Landsat or S2

# rescale the input images (for S2 images come in Uint16 0-10000
# for spot or landsat put the input value to 0-255
rescaleType='value' # 'value', 'percentile', 'std'
# for reflectanceRescale: 	if 'value': minSrc and maxSrc are the min-max values (be careful, must be Byte or Int depending on the input value)
#							if 'std': minSrc=-x, maxSrc=x, then min= average-x*std, max=average+x*std
#							if 'percentile': minSrc=a, maxSrc=b, min=percentile(a), max=percentile(b)
reflectanceRescale={'minSrc':0, 'maxSrc':255, 'minTrgt':0, 'maxTrgt':255} # example for rescaleType='value'
#reflectanceRescale={'minSrc':-2.5, 'maxSrc':2.5, 'minTrgt':0, 'maxTrgt':255} # example for rescaleType='std'
#reflectanceRescale={'minSrc':10, 'maxSrc':90, 'minTrgt':0, 'maxTrgt':255} # example for rescaleType='percentile'
IDField="FID"

#
# rescale image values
#___________________________________________________
def rescale(outFile, ds, scaleType, scaleParams, bandList, format, outputType, options):

    thisOut = gdal.GetDriverByName(format).Create(outFile, ds.RasterXSize, ds.RasterYSize, len(bandList), outputType, options=options )
    thisOut.SetProjection(ds.GetProjection())
    thisOut.SetGeoTransform(ds.GetGeoTransform())

    thisBand=1
    for ib in bandList:
        thisData = None
        thisData = numpy.array(ds.GetRasterBand(ib).ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)).astype(numpy.float32)

        if rescaleType == 'value':
            WTCmin = thisData <= scaleParams[0]
            WTCmax = thisData >= scaleParams[1]
            thisDataNew = scaleParams[2]+(scaleParams[3]-scaleParams[2])*(thisData - scaleParams[0])/float(scaleParams[1]-scaleParams[0])
            thisDataNew[WTCmin] = scaleParams[2]
            thisDataNew[WTCmax] = scaleParams[3]
        elif rescaleType == 'percentile':
            dataMinVal = numpy.percentile(thisData, scaleParams[0])
            dataMaxVal = numpy.percentile(thisData, scaleParams[1])
            if (dataMaxVal-dataMinVal) > 0:
                thisDataNew = scaleParams[2]+(scaleParams[3]-scaleParams[2])*(thisData - dataMinVal)/float(dataMaxVal-dataMinVal)
        elif rescaleType == 'std':
            average = thisData.mean()
            std = thisData.std()
            if std>0:
                dataMinVal = average + scaleParams[0]*std
                dataMaxVal = average + scaleParams[1]*std
                thisDataNew = scaleParams[2]+(scaleParams[3]-scaleParams[2])*(thisData - dataMinVal)/float(dataMaxVal-dataMinVal)
            else:
                thisDataNew = thisData * 0
        else:
            raise('Error unknown rescaleType {}'.format(rescaleType))

        thisOut.GetRasterBand(thisBand).WriteArray(thisDataNew, 0, 0)
        thisBand += 1
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
# extract information from file names
#
def extractInfo(thisName):
    date=None
    sensor=None
    # search Spot formatted dates YYYY-MM-DD
    m = re.search(r'[12][0-9][0-9][0-9]-[012][0-9]-[0123][0-9]', thisName)
    if m:
        dateTmp = m.group(0)
        dateComponents = dateTmp.split('-')
        date = '{}{}{}'.format(dateComponents[0], dateComponents[1], dateComponents[2])
    else: # search general dates YYYYMMDD
        m=re.search(r'[12][0-9][0-9][0-9][01][0-9][0123][0-9]', thisName)
        if m:
            date =m.group(0)

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
        sensor = s.group(0)
        return date, sensor

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

# _____________________________________________________________
#
# main code starts here
#
for thisDir in [rInDir, rOutDir, rRejectDir, duplicateDir]:
    if not os.path.isdir(thisDir):
        print 'Directory {} does not exists'.format(thisDir)
        sys.exit()


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
    print "Processing raster {}".format(os.path.basename(rr))
    ii = rasterBBox[rr]
    wkt = 'POLYGON(({} {}, {} {}, {} {}, {} {}, {} {}))'.format( ii[0][0], ii[0][1], ii[1][0], ii[1][1], ii[2][0], ii[2][1], ii[3][0], ii[3][1], ii[0][0], ii[0][1] )
    layer.SetSpatialFilter( ogr.CreateGeometryFromWkt(wkt) )

    if layer.GetFeatureCount() > 0:
        thisRaster = gdal.Open( rr, gdalconst.GA_ReadOnly)
        thisProjection = thisRaster.GetProjection()
        shpSpatialRef = osr.SpatialReference()
        shpSpatialRef.ImportFromEPSG(4326)
        transformation = osr.CoordinateTransformation(shpSpatialRef, osr.SpatialReference(wkt=thisProjection))

        iClip = 0
        for iFeat in layer:
            print '.',
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
            try:
                ds = gdal.Translate('', rr, format = 'MEM', projWin = [pointMin[0], pointMax[1], pointMax[0], pointMin[1]])
                date, sensor = extractInfo(os.path.basename(rr))
                outFileBasename = 'fid_{}_{}_{}.tif'.format(iFeat.GetFID(), date, sensor)
                if os.path.exists(os.path.join(rOutDir, outFileBasename)):
                    outFile = os.path.join(duplicateDir, outFileBasename)
                else:
                    if testValid(ds, testBand, testMinMax, testThreshold / 100.0):
                        outFile = os.path.join(rOutDir, outFileBasename)
                    else:
                        outFile = os.path.join(rRejectDir, outFileBasename)

                rescale( outFile, ds,
                 rescaleType,
                 scaleParams = [reflectanceRescale['minSrc'],reflectanceRescale['maxSrc'], reflectanceRescale['minTrgt'], reflectanceRescale['maxTrgt']],
                 bandList = exportBandList,
                 format='GTIFF',outputType = gdal.GDT_Byte,
                 options=['compress=lzw', 'bigtiff=IF_SAFER'])

            except Exception, e:
                print 'Error for file {}, iClip {}'.format(os.path.basename(rr), iClip)
                print '{}'.format(e)
            iClip += 1
            ds=None
        print ''



