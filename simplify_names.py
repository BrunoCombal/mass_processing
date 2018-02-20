import glob
import fnmatch
import os
import shutil
import string
import re

#inDir=u'Z://Processing/All_Kongo_images/Selection_Rep_of_Congo/Selection_Sentinel2_2016/Kongo_sentinel2_processed'
inDir=u'P://Selection_Sentinel2_2016/Kongo_sentinel2_processed'

outDir=u'E://tmp/machin/'

toRemove={'_OPER_PRD_MSIL1C_PDMC':'_MSIL1C', '.SAFE':''}

inFnames = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(inDir) for f in fnmatch.filter(files, '*.tif')]


iPos = 1
for ii in inFnames:
	thisBasename = os.path.basename(ii)
	for kk in toRemove:
		thisBasename = thisBasename.replace(kk, toRemove[kk])
	#print '{} -> {}'.format(ii, thisBasename)
	ROW = re.search('R[0-9][0-9][0-9]', thisBasename)
	if ROW:
		#print ROW.group(0)
		pass
	else:
		print 'not found'
	INIT = re.search('S2A_MSIL1C_([0-9]{8})', thisBasename)
	if INIT:
		#print INIT.group(0)
		pass
	else:
		print 'not found'
	newName = '{}_{}_{}.tif'.format(INIT.group(0), ROW.group(0), iPos)
	iPos += 1
	print iPos, thisBasename, newName, len(ii)
	try:
		shutil.copyfile(ii, os.path.join(outDir, newName))
	except IOError, e:
		print 'IOError {}'.format(e)
	except Exception, e:
		print 'Error {}'.format(e)
