import fnmatch
import os
import shutil
import gdal, gdalconst
import collections

#
# Checks if rasters files have the same checksum
# If some are identical: first is kept, other moved to another dir
# 
inDir='//ies.jrc.it/H03/Forobs_Export/verhegghen_export/Pour_Bruno/clip'
inFileFilter='*.tif'
duplicatesDir=''

# get list of files to check
# descend subdirs
inFnames = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(inDir) for f in fnmatch.filter(files, inFileFilter)]

hashDict={}
for ii in inFnames:
	thisBasename = os.path.basename(ii)

	thisDS = gdal.Open(ii, gdalconst.GA_ReadOnly)

	ret = gdal.Info(thisDS, format = 'json', deserialize = True, computeMinMax = False,
    	reportHistograms = False, reportProj4 = False,
    	stats = False, approxStats = False, computeChecksum = True,
    	showGCPs = False, showMetadata = False, showRAT = False,
    	showColorTable = False, listMDD = False, showFileList = False)

#	concatCkcksum=''
#	for iband in ret['bands']:
#		if 'checksum' in iband:
#			concatCkcksum = '{}{}'.format(concatCkcksum, iband['checksum'])
	concatCkcksum = ret['bands'][0]['checksum']

	hashDict[ii]=concatCkcksum # keep full path, to detect duplicates in sub folders

# now remove duplicates
myHash = [ii for ii in hashDict.values()]
sortedH = myHash.sort()
print sortedH
print myHash
