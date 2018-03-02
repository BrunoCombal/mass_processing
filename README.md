# mass_processing
Gdal/OGR script for processing large amount of files.
You can run them from the QGis python command line.

You must edit the scripts setting parameters.

* clipManyRasters.py: clip files and rescale their values, detect proportions of nodata and clouds, detects duplicates, sort the results in separate directories: output, bad clips, duplicates.
* simplify_names.py: change file names.
* rescaleManyRasters.py: changes multiple bands rasters data. Different possibilities: linear value rescale, standard deviations, rescale from min to max defined with distribution percentiles.