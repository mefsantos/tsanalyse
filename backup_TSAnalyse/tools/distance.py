# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Mara Matias

This file is part of HRFAnalyse.

    HRFAnalyse is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published
    by the Free Software Foundation, either version 3 of the License,
    or (at your option) any later version.

    HRFAnalyse is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with HRFAnalyse.  If not, see
    <http://www.gnu.org/licenses/>.

_______________________________________________________________________________

This module contains functions to calculates the distance between the
information in two files. The distance can be symmetrical or
asymmetrical depending if the value of the compression/entropy for the
concatenation of two files f1, f2 is the same whether you have f1.f2
or f2.f1.

Simetrical Distances:
Normalized Information Distance (compression)

Assymetrical Distances:
CrossEntropy (entropy): NOT IMPLEMENTED


ENTRY POINT: distance(filename1, filename2, distance_definition, compressor, 
level, decompress):
"""

import os
import sys
import compress
import tempfile


# ENTRY POINT FUNCTION
def distance(filename1, filename2, distance_definition, compressor, level, decompress):
    """Calculate the distance between two files.

    ARGUMENTS: String file name 1, String file name 2, String distance definition
    (nid, d1, d2), String compressor, int level, boolean decompress to decide 
    whether to time decompression or not.

    RETURN: A float that represents the distance between the two files.
    """
    method_to_call = getattr(sys.modules[__name__], distance_definition)
    return method_to_call(filename1, filename2, compressor, level, decompress)


# IMPLEMENTATION

# Normalized Information Distance
def nid(filename1, filename2, compressor, level, decompress):
    """
    DEFINITION: Use the compressor to calculate respectively c(f1.f2),c(f1) and
    c(f2) and calculate the distance acording to the definition of
    normalized information distance:

    d(f1,f2) = (c(f1.f2)-min{c(f1),c(f2)})/max{c(f1),c(f2)},

    where c is the chosen compressor,and an application of c to a file
    is the size of that file compressed (This formula is based on
    Kolmogorov complexity concepts).
    

    ARGUMENTS: String file name 1, String file name 2, String compressor, int level
    bool decompress.
    
    RETURN: A float that represents the distance between the two files.

    """
    file_total_data = []
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    with open(filename1, "r") as file1:
        file_total_data += file1.readlines()
    with open(filename2, "r") as file2:
        file_total_data += file2.readlines()
    for line in file_total_data:
        temp_file.write(line)
    temp_file.close()

    file1_cdata = compress.compress(filename1, compressor, level, decompress)[filename1]
    file2_cdata = compress.compress(filename2, compressor, level, decompress)[filename2]
    temp_file_cdata = compress.compress(temp_file.name,
                                        compressor,
                                        level,
                                        decompress)[temp_file.name]

    if decompress:
        dist = (temp_file_cdata.time - min(file1_cdata.time, file2_cdata.time)) / float(
                max(file1_cdata.time, file2_cdata.time))
    else:
        dist = (temp_file_cdata.compressed - min(file1_cdata.compressed, file2_cdata.compressed)) / float(
                max(file1_cdata.compressed, file2_cdata.compressed))

    os.unlink(temp_file.name)
    return dist


# Distance 1
def d1(filename1, filename2, compressor, level, decompress):
    """
    Use the compressor to calculate respectively c(f1.f2),c(f1) and
    c(f2) and calculate the distance acording to the definition
    presented by Mirko Degli Esposti , Chiara Farinelli , Marco
    Manca , Andrea Tolomelli in their article -- A similarity
    measure for biological signals: new applications to HRV analysis :

    d(f1,f2) =  max(c(f1.f2) − c(f1), c(f2.f1) − c(f2))/ max(c(f1), c(f2)),

    where c is the chosen compressor, and an application of c to a file
    is the size of that file compressed.
    

    Arguments: filename for both files, compressor, level of compression.
    
    Return: A float that represents the distance between the two
    files.

    Algorithm: Both files are opened and their content concatenated in
    a temporary file. Compression is then calculated for each file
    including the concatenation file, and the formula is applied.
    """

    file1_file2, file2_file1 = create_concatenated_files(filename1, filename2)

    file1_cdata = compress.compress(filename1, compressor, level, decompress)[filename1]
    file2_cdata = compress.compress(filename2, compressor, level, decompress)[filename2]
    file1_file2_cdata = compress.compress(file1_file2.name, compressor, level, decompress)[file1_file2.name]
    file2_file1_cdata = compress.compress(file2_file1.name, compressor, level, decompress)[file2_file1.name]

    if decompress:
        # this float conversion will become unecessary if the code is ever migrated to python3
        dist = max(file1_file2_cdata.time - file1_cdata.time, file2_file1_cdata.time - file2_cdata.time) / float(
                max(file1_cdata.time, file2_cdata.time))
    else:
        dist = max(file1_file2_cdata.compressed - file1_cdata.compressed,
                   file2_file1_cdata.compressed - file2_cdata.compressed) / float(
                max(file1_cdata.compressed, file2_cdata.compressed))

    # os.unlink(file1_file2.name)
    #    os.unlink(file2_file1.name)

    return dist


# Distance 2
def d2(filename1, filename2, compressor, level, decompress):
    """
    Use the compressor to calculate respectively c(f1.f2),c(f1) and
    c(f2) and calculate the distance acording to the definition
    presented by Mirko Degli Esposti , Chiara Farinelli , Marco
    Manca , Andrea Tolomelli in their article -- A similarity
    measure for biological signals: new applications to HRV analysis :

    d(f1,f2) = c(f1.f2) − c(f1) + c(f2.f1) − c(f2)/( 1/2*(c(f1.f2) + c(f2.f1)))

    where c is the chosen compressor, and an application of c to a file
    is the size of that file compressed.
    

    Arguments: filename for both files, compressor, level of compression.
    
    Return: A float that represents the distance between the two
    files.

    Algorithm: Both files are opened and their content concatenated in
    a temporary file. Compression is then calculated for each file
    including the concatenation file, and the formula is applied.
    """
    file1_file2, file2_file1 = create_concatenated_files(filename1, filename2)

    file1_cdata = compress.compress(filename1, compressor, level, decompress)[filename1]
    file2_cdata = compress.compress(filename2, compressor, level, decompress)[filename2]
    file1_file2_cdata = compress.compress(file1_file2.name, compressor, level, decompress)[file1_file2.name]
    file2_file1_cdata = compress.compress(file2_file1.name, compressor, level, decompress)[file2_file1.name]

    if decompress:
        dist = (file1_file2_cdata.time - file1_cdata.time + file2_file1_cdata.time - file2_cdata.time) / (
            1 / 2.0 * (file1_file2_cdata.time + file2_file1_cdata.time))
    else:
        dist = (file1_file2_cdata.compressed - file1_cdata.compressed + file2_file1_cdata.compressed -
                file2_cdata.compressed) / (1 / 2.0 * (file1_file2_cdata.compressed + file2_file1_cdata.compressed))

    os.unlink(file1_file2.name)
    os.unlink(file2_file1.name)

    return dist


# AUXILIARY FUNCTION

def create_concatenated_files(filename1, filename2):
    file1_file2 = tempfile.NamedTemporaryFile(delete=False)
    file2_file1 = tempfile.NamedTemporaryFile(delete=False)
    with open(filename1, "r") as file1:
        with open(filename2, "r") as file2:
            file1_data = file1.readlines()
            file2_data = file2.readlines()
            file1_file2_data = file1_data + file2_data
            file2_file1_data = file2_data + file1_data
    for line in file1_file2_data:
        file1_file2.write(line)
    for line in file2_file1_data:
        file2_file1.write(line)

    file1_file2.close()
    file2_file1.close()
    return file1_file2, file2_file1


def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """
    nid = parser.add_parser('nid',
                            help="Normalized Information Distance Definition( nid(f1,f2) = (c(f1.f2)-min{c(f1),c(f2)})/max{c(f1),c(f2)},)")

    d1 = parser.add_parser('d1',
                           help="Distance 1 ( d1(f1,f2) = max{c(f1.f2) − c(f1), c(f2.f1) − c(f2)}/ max{c(f1), c(f2)} ) proposed in the article --> http://www.dm.unibo.it/~farinell/paginelink/articolinostri/HRVLZ.pdf")

    d2 = parser.add_parser('d2',
                           help="Distance 2 ( d2(f1,f2) = c(f1.f2) − c(f1) + c(f2.f1) − c(f2)/( 1/2*(c(f1.f2) + c(f2.f1)))) proposed in the article --> http://www.dm.unibo.it/~farinell/paginelink/articolinostri/HRVLZ.pdf")

    compress.add_parser_options(nid)
    compress.add_parser_options(d1)
    compress.add_parser_options(d2)
