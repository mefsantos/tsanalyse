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
             multiscale_entropy(input_name,start,stop,step,entropy_function,*args,round_digits)
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
    import utility_functions as util
except ImportError:
    import tools.utility_functions as util


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
    as the original, where every s points are averages to generate a new one. If
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

    :param input_name: string containing the name of the dataset to read
    :param scales_dir: string containing the directory with the scales
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
        module_logger.info("Computing multiscale compression for directory %s"
                           % util.remove_project_path_from_file(input_name))
        filelist = util.listdir_no_hidden(input_name)
        for filename in filelist:
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

    else:
        module_logger.info("Computing multiscale compression for file %s"
                           % util.remove_project_path_from_file(input_name))
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
    module_logger.debug("Compression Table: %s" % compression_table)
    module_logger.info("Finished computing multiscale compression")
    return compression_table


def multiscale_entropy(input_name, scales_dir, start, stop, step, entropy_function, dimension, tolerance,
                       use_sd_tolerance=True, round_digits=None):
    """
    Calculate the multiscale entropy for a file or directory.

    :param input_name: string containing the name of the dataset to read
    :param scales_dir: string containing the directory with the multiple scales
    :param start: integer containing the starting scale
    :param stop: integer containing the ending scale
    :param step: integer containing the step between scales
    :param entropy_function: string containing the entropy algorithm to use
    :param dimension: integer containing the matrix dimension
    :param tolerance: float/double containing the tolerance to use
    :param use_sd_tolerance: boolean flag to decide whether or not to multiply the tolerance by the standard deviation
    :param round_digits: integer containing the numbers of digits to round to
    :return dictionary of 'string:EntropyData'
    """

    entropy_table = {}
    if os.path.isdir(input_name):
        module_logger.info("Computing multiscale entropy for directory %s"
                           % util.remove_project_path_from_file(input_name))
        filelist = util.listdir_no_hidden(input_name)
        files_stds = calculate_std(os.path.join("%s_Scales" % input_name, "Scale %d" % start))
        tolerances = dict((filename, files_stds[filename] * tolerance) for filename in files_stds)

        if not use_sd_tolerance:
            module_logger.info("Tolerance does not include Standard Deviation")
            tolerances = dict(zip(files_stds.keys(), [tolerance] * len(files_stds)))
        else:
            module_logger.info("Tolerance includes Standard Deviation")

        for filename in filelist:

            entropy_table[filename] = []
            for scale in range(start, stop, step):
                file_in_scale = os.path.join("%s_Scales" % input_name, "Scale %d" % scale, filename)
                try:
                    entropy_results = entropy(file_in_scale, entropy_function, dimension,
                                          {filename: tolerances[filename]}, round_digits)
                except ValueError as ve:
                    module_logger.error("%s." % ve)
                    break
                except KeyError as ke:
                    module_logger.error("Key %s does not exist. Skipping file '%s'..."
                                        % (ke, util.remove_project_path_from_file(filename)))
                    break
                else:
                    try:
                        entropy_table[filename].append(entropy_results[filename].entropy)
                    except AttributeError as ate:
                        module_logger.error("%s" % ate)
    else:
        module_logger.info("Computing multiscale entropy for file '%s'" % util.remove_project_path_from_file(input_name))
        filename = os.path.basename(input_name)
        file_for_std = os.path.join(scales_dir, "Scale %d" % start, filename)
        try:
            file_std = calculate_std(file_for_std)
        except ValueError as ve:
            module_logger.error("%s" % ve)
            module_logger.warning("Skipping file '%s'" % filename)
        except IndexError as ixe:
                module_logger.critical("%s - The file '%s' does not conform to the requisites:"
                                       " one column with the hrf vales."
                                       % (ixe, util.remove_project_path_from_file(filename)))
        else:
            tolerances = dict((filename, file_std[fname] * tolerance) for fname in file_std)
            if not use_sd_tolerance:
                module_logger.info("Tolerance does not include Standard Deviation")
                tolerances = dict(zip(file_std.keys(), [tolerance] * len(file_std)))
            else:
               module_logger.info("Tolerance includes Standard Deviation")

            entropy_table[filename] = []
            for scale in range(start, stop, step):
                file_in_scale = os.path.join(scales_dir, "Scale %d" % scale, filename)
                try:
                    entropy_results = entropy(file_in_scale, entropy_function, dimension, tolerances, round_digits)
                except ValueError as ve:
                    module_logger.error("%s" % ve)
                    break
                except IndexError as ixe:
                    module_logger.critical("%s - The file '%s' does not conform to the requisites:"
                                           " one column with the hrf vales."
                                           % (ixe, util.remove_project_path_from_file(filename)))
                    break
                else:
                    entropy_table[filename].append(entropy_results[filename].entropy)

    module_logger.debug("Entropy Table: %s" % entropy_table)
    module_logger.info("Finished computing multiscale entropy")
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

    # with open(inputfile, "rU") as fdin:
    #     lines = fdin.readlines()
    #     lines = list(map(float, lines))
    #

    # -1 to read the last available column
    lines = util.readlines_with_col_index(inputfile, col_index=-1, as_type=float)
    # lets force a type cast to float so the error can be caught outside
    lines = list(map(float, lines))
    # print(lines)

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
    return


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
                        help="Start scales with this amount of points. Default:[%(default)s]",
                        default=1)
    parser.add_argument("-stop",
                        "--scale-stop",
                        metavar="SCALE",
                        type=int,
                        dest="scale_stop",
                        action="store",
                        help="Stop scales with this amount of points. Default:[%(default)s]",
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
                        help="before calculating the resulting scale, multiply every number in the series by MUL ORDER;"
                             " -1 disables this option; Default:[%(default)s]",
                        default=-1)
    parser.add_argument("-rint",
                        "--round-to-int",
                        dest="round",
                        action="store_true",
                        help="Round the scales values to int.",
                        default=False)
    parser.add_argument("-ks",
                        "--keep-scales",
                        dest="keep_scales",
                        action="store_true",
                        help="After multiscale processing maintain the generated scales",
                        default=False)
