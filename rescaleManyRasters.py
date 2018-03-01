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
#rInDir=u'z://Processing/All_Kongo_images/Selection_Rep_of_Congo/Selection_Spot2010/Spot4_5' # raster input dir
rInDir=u'F://2017'

#Output directory - create 3 folders to store the good, bad and duplicate clips
rOutDir=u'E://tmp/zetest' #clip output dir

#select rule of the images to clip in the input directory
selectRule=u'*.tif' # wildcard rule


# rescale the input images (for S2 images come in Uint16 0-10000
# for spot or landsat put the input value to 0-255
rescaleType='std' # 'value', 'percentile', 'std'
# for reflectanceRescale: 	if 'value': minSrc and maxSrc are the min-max values (be careful, must be Byte or Int depending on the input value)
#							if 'std': minSrc=-x, maxSrc=x, then min= average-x*std, max=average+x*std
#							if 'percentile': minSrc=a, maxSrc=b, min=percentile(a), max=percentile(b)
#reflectanceRescale={'minSrc':500, 'maxSrc':3000, 'minTrgt':0, 'maxTrgt':255} # example for rescaleType='value'
reflectanceRescale={'minSrc':-2, 'maxSrc':2, 'minTrgt':0, 'maxTrgt':255} # example for rescaleType='std'
#reflectanceRescale={'minSrc':1, 'maxSrc':99, 'minTrgt':0, 'maxTrgt':255} # example for rescaleType='percentile'


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
            WTCmin = thisData <= dataMinVal
            WTCmax = thisData >= dataMaxVal
            thisDataNew = scaleParams[2]+(scaleParams[3]-scaleParams[2])*(thisData - dataMinVal)/float(dataMaxVal-dataMinVal)
        elif rescaleType == 'std':
            average = thisData.mean()
            std = thisData.std()
            dataMinVal = average + scaleParams[0]*std
            dataMaxVal = average + scaleParams[1]*std
            wOutMax = thisData > dataMaxVal
            wOutMin = thisData < dataMinVal
            thisDataNew = scaleParams[2]+(scaleParams[3]-scaleParams[2])*(thisData - dataMinVal)/float(dataMaxVal-dataMinVal)
            thisDataNew[wOutMax] = scaleParams[3]
            thisDataNew[wOutMin] = scaleParams[2]
        else:
            raise('Error unknown rescaleType {}'.format(rescaleType))

        thisOut.GetRasterBand(thisBand).WriteArray(thisDataNew, 0, 0)
        thisBand += 1
#
# main code starts here
#
if not os.path.isdir(rInDir):
    print 'Directory {} does not exists'.format(rInDir)
    sys.exit()
if not os.path.isdir(rOutDir):
    try:
        os.makedirs(rOutDir)
    except IOError:
        print 'Could not create output directory {}'.format(rOutDir)
        sys.exit()

# rInDir and rOutDir must be different
if rInDir == rOutDir:
    print 'input and output directories must be different'
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

for rr in inRasterFnames:
    thisRaster = gdal.Open( rr, gdalconst.GA_ReadOnly)

    try:
        # test no-data
        outFileBasename = os.path.basename(rr)
        outFile = os.path.join(rOutDir, outFileBasename)

        rescale( outFile, thisRaster,
                rescaleType,
                scaleParams = [reflectanceRescale['minSrc'],reflectanceRescale['maxSrc'], reflectanceRescale['minTrgt'], reflectanceRescale['maxTrgt']],
                bandList = range(1, thisRaster.RasterCount+1, 1),
                format='GTIFF',outputType = gdal.GDT_Byte,
                options=['compress=lzw', 'bigtiff=IF_SAFER'])

    except Exception, e:
        #print 'Error for file {}, iClip {}'.format(os.path.basename(rr))
        print '{}'.format(e)
        print [pointMin[0], pointMin[1], pointMax[0], pointMax[1]]
        print thisRaster.GetGeoTransform()



