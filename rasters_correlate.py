import fnmatch
import os
import shutil
import gdal, gdalconst
import numpy
from scipy.stats.stats import pearsonr

#
# Checks existence of correlated images in a list
# If some are identical: first is kept, other moved to another dir
# 
inDir='//ies.jrc.it/H03/Forobs_Export/verhegghen_export/Pour_Bruno/clip'
inFileFilter='*.tif'
uniqueDir='E://tmp/unique'
duplicatesDir='E://tmp/discard'

#
# functions
#
def correlation(ref, test):
	dataRef = numpy.ravel(ref.GetRasterBand(1).ReadAsArray(0, 0, ref.RasterXSize/2, ref.RasterYSize/2))
	dataTest = numpy.ravel(test.GetRasterBand(1).ReadAsArray(0, 0, test.RasterXSize/2, test.RasterYSize/2))
	if ref.RasterXSize != test.RasterXSize:
		return [None, None]
	if ref.RasterYSize != test.RasterYSize:
		return [None, None]
	#return numpy.corrcoef(dataRef, dataTest)[0]
	return pearsonr(dataRef, dataTest)

# get list of files to check
# descend subdirs
inFnames = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(inDir) for f in fnmatch.filter(files, inFileFilter)]

hashDict={}
for ii in inFnames:
	thisBasename = os.path.basename(ii)

	curList = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(inDir) for f in fnmatch.filter(files, inFileFilter)]
	for jj in curList: # to be recomputed as files are moved away
		if ii != jj:
			refDS = gdal.Open(ii, gdalconst.GA_ReadOnly)
			testDS = gdal.Open(jj, gdalconst.GA_ReadOnly)
			try:
				corr = correlation(refDS, testDS)
				if corr[0] is None:
					print '-'
				else:
					if corr[0]>0.9:
						print corr, os.path.basename(ii), os.path.basename(jj)
						shutil.move(jj, duplicatesDir)
					else:
						print corr
			except Exception, e:
				print 'Error {} with files {} and {}'.format(e, os.path.basename(ii), os.path.basename(jj))
			refDS = None
			testDS = None
	shutil.move(ii, uniqueDir)

# end of script
