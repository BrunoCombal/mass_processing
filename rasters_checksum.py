import glob
import fnmatch
import os
import shutil
import string
import re
import sys


#
# Checks if rasters files have the same checksum
# If some are identical: first is kept, other moved to another dir
# 
inDir=''
inFileFilter='*.tif'
checkBand=[1] # list of bands to check
duplicatesDir=''

# get list of files to check
inFnames = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(inDir) for f in fnmatch.filter(files, inFileFilter)]

hashDict={}
for ii inFnames:
	thisBasename = os.path.basename(ii)
	