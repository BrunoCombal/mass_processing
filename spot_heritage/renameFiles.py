import os
import fnmatch
import xml.etree.ElementTree as ET
import os.path
import shutil


inDir='//ies.jrc.it/H03/FOROBS/optical1/afr/spot/spot_afd/Pivot_2015/Ortho'
outDir='E:/tmp/exportSpot'
renameList={}

for root, dirnames, filenames in os.walk(inDir):
	for filename in fnmatch.filter(filenames, 'IMAGERY.TIF'):
		xmlFile = os.path.join(root, 'METADATA.DIM')
		tree = ET.parse(xmlFile)
		rootXML = tree.getroot() 

		thisDate = rootXML.findall('.//IMAGING_DATE')[0].text # is a string
		thisULX = rootXML.findall('.//FRAME_LON')[0].text
		thisULY = rootXML.findall('.//FRAME_LAT')[0].text
		thisMission = rootXML.findall('.//MISSION_INDEX')[0].text
		thisSourceID = rootXML.findall('.//SOURCE_ID')[0].text

		#newName = 'SPOT_{}_{}_{}_{}.tif'.format(thisMission, thisDate, thisULX, thisULY)
		newName = 'SPOT_{}_{}_{}.tif'.format(thisMission, thisDate, thisSourceID)
		print os.path.join(root, filename), ' --> ', os.path.join(outDir,newName)
		#shutil.copyfile(os.path.join(root, filename), os.path.join(outDir,newName))
		

# end of code