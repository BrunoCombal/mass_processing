# Split a CSV file in many smaller files
import os

# parameters
inFile='E:/pts_CE_2018-02-21.csv' # input file
outName='E:/split/split'
withHeader=True
csvfileTmp = open(inFile, 'r').readlines()
if withHeader:
	header = csvfileTmp[0]
csvfile = csvfileTmp[1:]
nSplit = 8
sizeSplit = len(csvfile) / nSplit

fileNum = 1
for i in range(0,len(csvfile)):
	if i % sizeSplit == 0:
		thisOut = open('{}_{}.csv'.format(outName, str(fileNum)), 'w+')
		if withHeader:
			thisOut.writelines(header)
		thisOut.writelines(csvfile[i:i+sizeSplit])
		fileNum += 1

