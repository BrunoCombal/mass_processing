# Split a CSV file in many smaller files
import os

inFile='mycsv.csv'
withHeader=True
csvfile = open(inFile, 'r').readlines()
nSplit = 8
sizeSplit = len(csvfile) / nSplit

if withHeader:
	header = csvfile[0]

filename = 1
for i in range(1,len(csvfile)):
	if i % sizeSplit == 0:
		thisOut = open(str(filename) + '.csv', 'w+')
		if withHeader:
			thisOut.writelines(header)
		thisOut.writelines(csvfile[i:i+1000])
		filename += 

