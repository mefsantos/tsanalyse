[![Coverage Status](https://coveralls.io/repos/github/mefsantos/tsanalyse/badge.svg?branch=master)](https://coveralls.io/github/mefsantos/tsanalyse?branch=master)


## Installation Notes

The tool set requires some external libraries described in _Requirements.txt_, along with instructions.
**env_setup.sh** script automatically install and link all the dependencies required for UBUNTU systems.
Moreover, the following examples refer to an existing folder, however as the functions require different inputs, 
 the name 'unittest_dataset' in in some examples is merely a placeholder.

## Documentation

The tool set is extensively documented using pydoc. To launch the graphical interface run:

        pydoc -g

in the command line.

## TSAnalyseDirect

The main interface TSAnalyseDirect allows for operations to be applied to files or directories (no subdirectories):


### Examples :


* Filter
     
    Retrieve the hrf:
        
        ./TSAnalyseDirect.py unittest_dataset filter
    
    Retrieve the timestamps and hrf:
        
        ./TSAnalyseDirect.py unittest_dataset filter -kt
    
    Retrieve the hrf of the file discarding the first 60 seconds
        
        ./TSAnalyseDirect.py unittest_dataset filter -ds 60
    
    Retrieve the hrf from first 2000 lines:
        
        ./TSAnalyseDirect.py unittest_dataset filter -s 2000 --use_lines


* Compress
     
    Compress using the gzip algorithm (maximum compression level will be used)
        
        ./TSAnalyseDirect.py unittest_dataset compress -c gzip

    Compress using the brotli algorithm (maximum compression level will be used) and return an additional column with
    the compression ratio

        ./TSAnalyseDirect.py unittest_dataset compress -c brotli -cr

    Compress using the bzip2 algorithm with minimum compression(1 in this case):
        
        ./TSAnalyseDirect.py unittest_dataset compress -c bzip2 --level 1


* Entropy
    
    Calculate the entropy using Approximate entropy with tolerance 0.2 and matrix
    dimension 2 (reference values for the analysis of biological data)
     
        ./TSAnalyseDirect.py unittest_dataset entropy apen -t 0.2

* Stv
	Compute short-term variability using the Arduini algorithm

		./TSAnalyse.py unittest_dataset_filtered stv -algo arduini

## TSAnalyseFileBlocks

The auxiliary interface TSAnalyseFileBlocks does the partition and compression of the file blocks
automatically.

### Examples:


* Compress

       Cut files into 5min blocks with no overlap and compress each one with the default compressor
        
        ./TSAnalyseFileBlocks.py unittest_dataset/ -s 300 compress
        
        
       Cut files into blocks with 300 lines with no overlap and compress each one with the default compressor
        
        ./TSAnalyseFileBlocks.py unittest_dataset/ -s 300 --use-lines compress


* Entropy
    
       Cut files into blocks with 5 min where one block starts 1 min later then the previous one did.
       Calculate each files entropy using the Sample entropy.
        
        ./TSAnalyseFileBlocks.py unittest_dataset/ -s 300 -g 60 entropy sampen


## TSAnalyseMultiScale

The last interface TSAnalyseMultiScale is specific to calculate MultiScale entropy and compression:

### Examples:

* Multiscale entropy for all the files starting at scale 1(original files) and ending in scale 20

        ./TSAnalyseMultiscale unittest_dataset entropy sampen

* Multiscale compression with rounded results for scale, since the scales are constructed
by averaging a given number of point we are bound to have floats, this options
rounds those numbers to an integer.

        ./TSAnalyseMultiscale unittest_dataset --round-to-int compression

* Multiscale compression with rounded results for scale, multiplyed by 10, the scale
point is multiplied by 10 and rounded.
    
        ./TSAnalyseMultiscale unittest_dataset --round-to-int --multiply 10 compression -c paq8l

_______________________________________________________________________________

    Copyright (C) 2012 Mara Matias
    Edited by Marcelo Santos - 2016

    This file is part of TSAnalyse.

    TSAnalyse is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published
    by the Free Software Foundation, either version 3 of the License,
    or (at your option) any later version.

    TSAnalyse is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with TSAnalyse.  If not, see
    <http://www.gnu.org/licenses/>.
