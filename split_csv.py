# Split a CSV file in many smaller files
import os

# parameters
inFile='E:/pts_CE_2018-02-21.csv' # input file
outName='E:/split/split'
withHeader=True
csvfile = open(inFile, 'r').readlines()
nSplit = 8
sizeSplit = len(csvfile) / nSplit

if withHeader:
	header = csvfile[0]

fileNum = 1
for i in range(1,len(csvfile)):
	if i % sizeSplit == 0:
		thisOut = open('{}_{}.csv'.format(outName, str(fileNum)), 'w+')
		if withHeader:
			thisOut.writelines(header)
		thisOut.writelines(csvfile[i:i+1000])
		fileNum += 1

