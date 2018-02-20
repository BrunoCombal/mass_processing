import glob
import fnmatch
import os
import shutil
import string
import re
import sys

# Note for MS-Windows users: Windows does not support filename and paths longer than 160 characters.
# Use a drive letter to shorten the path, by pointing it to the directory you wish to process.
# for example: 
# inDir=u'Z://Processing/All_Kongo_images/Selection_Rep_of_Congo/Selection_Sentinel2_2016/Kongo_sentinel2_processed'
# can be set to:
# inDir=u'P://Selection_Sentinel2_2016/Kongo_sentinel2_processed'

# Input parameters
# ----------------
# inDir: input directory where are the files to be renamed
# inFileFilter: a string indicating which file to consider in the input directory. For example: '*.tif' to keep files ending with .tif,
# 'SPOT5_*.img' to keep files starting with SPOT5 and ending with img, '*_2017*.tif' for files with string 2017 ending with tif.
# to replace: a list of sub-string, with their replacement. Use an empty string '' to delete a substring.
# the syntax is toReplace={substring1: replacement1, substring2:replacement2, substring3, replacement3}
# Add as many pair substring:replacement as your need.
# outDir: output directory, where the input files will be copied, with a shorten name
# useCounter: True or False. If True add a counter at the end of the filename (used for debbugging, to check files are unique)
# ----------------
# How it works: the script get the list of files from inDir,
# create a new filename by changing substrings in the original filenames with the corresponding replacements,
# then create a copy in outDir with the new name.

inDir=u'P://Selection_Sentinel2_2016/Kongo_sentinel2_processed'
inFileFilter='*.tif'
toReplace={'_OPER_PRD_MSIL1C_PDMC':'_MSIL1C', '.SAFE':''}
outDir=u'E://tmp/machin/'
useCounter=False

# -----------------
# script
# edit with caution
# -----------------

# get list of input files
inFnames = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(inDir) for f in fnmatch.filter(files, inFileFilter)]
if len(inFnames)==0:
	print 'No input file to process!'
	sys.exit(1)

iPos = 1
for ii in inFnames:
	thisBasename = os.path.basename(ii)
	for kk in toReplace:
		thisBasename = thisBasename.replace(kk, toReplace[kk])

	ROW = re.search('R[0-9][0-9][0-9]', thisBasename)
	if not ROW:
		print 'ROW not found in {}'.format(thisBasename)
	INIT = re.search('S2A_MSIL1C_([0-9]{8})', thisBasename)
	if not INIT:
		print 'INIT sequence not found in {}'.format(thisBasename)

	if useCounter:
		newName = '{}_{}_{}.tif'.format(INIT.group(0), ROW.group(0), iPos)
	else:
		newName = '{}_{}.tif'.format(INIT.group(0), ROW.group(0))
	iPos += 1

	try:
		shutil.copyfile(ii, os.path.join(outDir, newName))
	except IOError, e:
		print 'IOError {}'.format(e)
	except Exception, e:
		print 'Error {}'.format(e)

# end of script