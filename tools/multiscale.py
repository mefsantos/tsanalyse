"""
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

_______________________________________________________________________________

This module creates the multiple scales for a file or all the files in
a directory.

A scale is related to the number of points in a time series in this
case the practical creation of a scale N is achieved by taking every N
numbers and transforming them into one by calculating their mean.

Once the scales are created you can use this module to compress or calculate the 
entropy of the different scales.

MODULE DEPENDENCIES:
numpy(http://numpy.scipy.org/)

ENTRY POINT: create_scales(input_name,dest_dir,start,stop,step,mul_order,round_to_int)
             multiscale_compression(input_name,start,stop,step,compressor,level,decompress, with_compression_rate)
             multiscale_entropy(input_name,start,stop,step,entropy_function,*args)
"""

import os
import numpy
import logging

try:
    from tools.compress import compress
except ImportError:
    from compress import compress
try:
    from tools.entropy import entropy, calculate_std

except ImportError:
    from entropy import entropy, calculate_std

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util


module_logger = logging.getLogger('tsanalyse.multiscale')

# ENTRY POINT FUNCTION


def create_scales(input_name, dest_dir, start, stop, step, mul_order, round_to_int):
    """
    Creates all the scales in a given interval.

    ARGUMENTS: String name of input directory/file, String name of the output
    directory, int first scale to be calculated, int last scale to be
    calculated, int jump between one scale and the next, int mul_order, bool 
    round_to_int.

    RETURN: None.
    
    ALGORITHM:Create a new folder for each scale between start and stop (use step 
    to jump between scale numbers). For each scale(s) build file with the same name 
    as the original, where every s points are avareges to generate a new one. If
    mul_order is not disabled (set to -1) when calculating a scale point multiply
    all the original points by that mul_order. If round_to_int is set to True round
    the resulting scale point and output only the integer value.

    :param input_name: path for the dataset to read
    :param dest_dir: name of the destination directory
    :param start: starting scale
    :param stop: ending scale
    :param step: step between scales
    :param mul_order: multiplication order to apply to the time series
    :param round_to_int: flat to round the time series to integer
    """
    for scale in range(start, stop, step):
        output_dir = os.path.join(dest_dir, "Scale %d" % scale)
        if not os.path.isdir(output_dir):
            module_logger.info("Creating Scale %d..." % scale)
            os.makedirs(output_dir)
        else:
            module_logger.warning("Scale %d exists, skipping..." % scale)
            continue
        if os.path.isdir(input_name):
            filelist = util.listdir_no_hidden(input_name)
            for filename in filelist:
                create_scale(os.path.join(input_name, filename.strip()),
                             output_dir,
                             scale,
                             mul_order,
                             round_to_int)
        else:
            create_scale(input_name.strip(),
                         output_dir,
                         scale,
                         mul_order,
                         round_to_int)


def multiscale_compression(input_name, scales_dir, start, stop, step, compressor, level, decompress,
                           with_compression_rate, round_digits=None):
    """
    Calculate the multiscale compression for a file or directory.
    
    ARGUMENTS: String input file/directory name, int start scale, int stop scale,
    int step between scales, String compressor, int level, bool decompress.
    
    RETURN: Dictionary with filenames as keys and an array of CompressionData
    (one for each scale) as values.

    :param input_name: name of the dataset to read
    :param scales_dir: directory containing the scales
    :param start: starting scale
    :param stop: ending scale
    :param step: step between scales
    :param compressor: compressor to use
    :param level: level of compression
    :param decompress: flag to enable the output of the decompression time
    :param with_compression_rate: flag to enable the calculation of the compression rate
    :param round_digits: number of decimal digits to use when rounding floats/doubles
    :return dictionary of 'string:CompressionData'
    """

    compression_table = {}
    if os.path.isdir(input_name):
        filelist = util.listdir_no_hidden(input_name)
        for filename in filelist:
            compression_table[filename] = []
            for scale in range(start, stop, step):
                # file_to_compress = os.path.join("%s_Scales" % input_name, "Scale %d" % scale, filename)
                file_to_compress = os.path.join(scales_dir, "Scale %d" % scale, filename)
                compression_results = compress(file_to_compress, compressor, level, decompress,
                                               with_compression_rate, round_digits)

                compression_table[filename].append(compression_results[filename].original)
                compression_table[filename].append(compression_results[filename].compressed)
                if with_compression_rate:
                    compression_table[filename].append(compression_results[filename].compression_rate)
                if decompress:
                    compression_table[filename].append(compression_results[filename].time)

    else:
        # TODO: use the "home" dir of datasets when the input is a single file - solved?
        # TODO: fix the following code - produces bugs - solved?
        filename = os.path.basename(input_name)
        compression_table[filename] = []
        for scale in range(start, stop, step):
            file_to_compress = os.path.join(scales_dir, "Scale %d" % scale, filename)

            compression_results = compress(file_to_compress, compressor, level, decompress,
                                           with_compression_rate, round_digits)

            compression_table[filename].append(compression_results[filename].original)
            compression_table[filename].append(compression_results[filename].compressed)

            if with_compression_rate:
                compression_table[filename].append(compression_results[filename].compression_rate)

            if decompress:
                compression_table[filename].append(compression_results[filename].time)

    return compression_table


def multiscale_entropy(input_name, scales_dir, start, stop, step, entropy_function, dimension, tolerance):
    """
    Calculate the multiscale entropy for a file or directory.

    ARGUMENTS: String input file/directory name, int start scale, int stop scale,
    int step between scales, String compressor, int dimension, float tolerance

    RETURN: Dictionary with filenames as keys and an array of EntropyData (one
    for each scale) as values.

    :param input_name: name of the dataset to read
    :param scales_dir: directory containing the multiple scales
    :param start: starting scale
    :param stop: ending scale
    :param step: step between scales
    :param entropy_function: entropy algorithm to use
    :param dimension: matrix dimension
    :param tolerance: tolerance to use
    :return dictionary of 'string:EntropyData'
    """

    entropy_table = {}
    if os.path.isdir(input_name):
        filelist = util.listdir_no_hidden(input_name)
        files_stds = calculate_std(os.path.join("%s_Scales" % input_name, "Scale %d" % start))
        tolerances = dict((filename, files_stds[filename] * tolerance) for filename in files_stds)
        for filename in filelist:
            entropy_table[filename] = []
            for scale in range(start, stop, step):
                file_in_scale = os.path.join("%s_Scales" % input_name, "Scale %d" % scale, filename)
                entropy_results = entropy(file_in_scale,
                                          entropy_function,
                                          dimension,
                                          {filename: tolerances[filename]})
                entropy_table[filename].append(entropy_results[file_in_scale][1])
    else:
        filename = os.path.basename(input_name)
        file_for_std = os.path.join(scales_dir, "Scale %d" % start, filename)
        file_std = calculate_std(file_for_std)

        tolerances = dict((filename, file_std[fname] * tolerance) for fname in file_std)

        entropy_table[filename] = []
        for scale in range(start, stop, step):
            file_in_scale = os.path.join(scales_dir, "Scale %d" % scale, filename)
            entropy_results = entropy(file_in_scale,
                                      entropy_function,
                                      dimension,
                                      tolerances)

            entropy_table[filename].append(entropy_results[filename].entropy)
    return entropy_table


# IMPLEMENTATION
def create_scale(inputfile, output_dir, scale, mul_order, round_to_int):
    """
    This function creates a one scale for one file.

    ARGUMENTS: String name of file, String directory where resulting file should
    be saved,int scale size,int mul_order, bool round_to_int.

    RETURN: None

    ALGORITHM: For a scale N, read the file, on each iteration extract an interval
    of N values, calculate the mean of these numbers and save it in the resulting
    file. Each iteration's interval starts after the last number used in the
    previous iteration.

    :param inputfile: file to read
    :param output_dir: output directory
    :param scale: current scale being processed
    :param mul_order: order of multiplication
    :param round_to_int: flag to round the time series to integer

    """
    filename = os.path.basename(inputfile)
    line_index = 0
    with open(inputfile, "rU") as fdin:
        lines = fdin.readlines()
        lines = list(map(float, lines))
    with open(os.path.join(output_dir, filename), "w") as fdout:
        while line_index + scale <= len(lines):
            scaled_hrf = numpy.mean(lines[line_index:line_index + scale])
            if mul_order != -1:
                scaled_hrf *= mul_order
            if round_to_int:
                fdout.write('%d\n' % round(scaled_hrf))
            else:
                fdout.write('%.3f\n' % scaled_hrf)
            line_index += scale


# AUXILIARY FUNCTIONS
def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    ARGUMENTS: The parser to which you want the arguments added to.

    RETURN:None
    """

    parser.add_argument("-start",
                        "--scale-start",
                        metavar="SCALE",
                        type=int,
                        dest="scale_start",
                        action="store",
                        help="Start scales whith this amount of points. Default:[%(default)s]",
                        default=1)
    parser.add_argument("-stop",
                        "--scale-stop",
                        metavar="SCALE",
                        type=int,
                        dest="scale_stop",
                        action="store",
                        help="Stop scales whith this amount of points. Default:[%(default)s]",
                        default=20)
    parser.add_argument("-step",
                        "--scale-step",
                        metavar="STEP",
                        type=int,
                        dest="scale_step",
                        action="store",
                        help="Step between every two scales.Default:[%(default)s]",
                        default=1)
    parser.add_argument("-mult",
                        "--multiply-by-order",
                        metavar="MUL ORDER",
                        type=int,
                        dest="mul_order",
                        action="store",
                        help="before calculating the resulting scale, multiply every number in the series by MUL ORDER, -1 disables this option; Default:[%(default)s]",
                        default=-1)
    parser.add_argument("-rint",
                        "--round-to-int",
                        dest="round",
                        action="store_true",
                        default=False)
