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

MODULE DEPENDENCIES: 
numpy(http://numpy.scipy.org/)

This modules objective is to study the block's in a file os files in a
directory and mark the blocks that are above and below certain
limits. The descriptions always mention compression and not entropy
simply because this was until now only used with compression,
In terms of application, this would also work for an entropy dictionary.
 
We used two definitions of limits:
  mean +/- std
  outliers (Percentil(50) +/- Inter Percentil Ratio * 1.5)(1)


(1)Note:There are other more strict definitions of outliers this one was
chosen because it was well adapted to our dataset.


This module's entry point function is apply_metric(...)
"""
import numpy
import logging

module_logger = logging.getLogger('tsanalyse.separate_blocks')


# ENTRY POINT FUNCTION

def apply_metric(compressed_files, block_times, metric):
    """
    Apply the metric chosen to separate the blocks in all the files in
    compressed files.

    Arguments:Dictionary with filenames as keys and each file's
    resulting compression dictionary as value, dictionary whith
    filenames as keys and each file's resulting block times list as
    value, the metric to be applied.

    Return: A pair of dictionaries with filenames as keys and the
    file's below_lower or above_upper dictionaries as values.

    """
    below_lower = {}
    above_upper = {}
    # A single file
    if len(compressed_files.keys()) == 1:
        blocks_below, blocks_above = apply_metric_file(compressed_files.values()[0], block_times.values()[0], metric)
        below_lower[compressed_files.keys()[0]] = blocks_below
        above_upper[compressed_files.keys()[0]] = blocks_above
    else:
        for filename in compressed_files:
            blocks_below, blocks_above = apply_metric_file(compressed_files[filename], block_times[filename], metric)
            below_lower[filename] = blocks_below
            above_upper[filename] = blocks_above
    return below_lower, above_upper


# IMPLEMENTATION

def apply_metric_file(compressed_blocks, block_times, metric):
    """
    Apply the metric chosen to the data of a single file to determine
    the upper and lower limits, and mark blocks that are either above
    or below respectively.

    Arguments:Dictionary with filenames(the blocks produced by one
    file) as keys and the respective original and compressed sizes, a
    list with the file's respective block times in seconds, and the
    metric to be used.

    Return: A pair of dictionaries with the blocks above the upper
    limit and below the lower limits, where the block number is used
    as key and the real start and end times as values.

    Algorithm: The compression dictionary is used to mark (the block
    number and real start and end times in seconds are saved) every
    partition whose size is bellow the lower limit or above the upper
    limit. The marked blocks are written to a .csv file.
    """
    compression_sizes = [compressed_blocks[fileblock].compressed for fileblock in compressed_blocks]
    if metric == 'mean_std':
        lower_lim, upper_lim = mean_std(compression_sizes)
    elif metric == 'outliers':
        lower_lim, upper_lim = outliers(compression_sizes)
    below_lower = {}
    above_upper = {}

    for fileblock in compressed_blocks:
        # fileblock is alway something like filename_blocknum
        block = int(fileblock.split('_')[-1])
        start_second = round(block_times[block - 1][0], 2)
        end_second = round(block_times[block - 1][1], 2)
        if compressed_blocks[fileblock][1] < lower_lim:
            below_lower[block] = (start_second, end_second)
        elif compressed_blocks[fileblock][1] > upper_lim:
            above_upper[block] = (start_second, end_second)

    return below_lower, above_upper


def mean_std(compressed_sizes):
    """
    Defines the limits using the mean and standard deviation.
    
    Arguments:List with compressed file sizes.
    
    Return: A tuple with lower limit, and upper limit.

    Lower limit is defined as mean - standard deviation
    Upper limit is defined as mean + standard deviation 
    """
    mean_size = numpy.mean(compressed_sizes)
    std_size = numpy.std(compressed_sizes)
    upper_lim = mean_size + std_size
    lower_lim = mean_size - std_size

    return lower_lim, upper_lim


def outliers(compressed_sizes):
    """
    Defines the limits based on the definition of outliers.

    Arguments:Dictionary with compressed file sizes as values.
    
    Return: A tuple with lower limit, and upper limit.

    Lower limit = Percentil(50) - Inter Percentil Ratio * 1.5
    Upper limit = Percentil(50) + Inter Percentil Ratio * 1.5

    where,
    Inter Percentil Ratio = Percentil(75)-Percentil(25)
    """
    ordered_sizes = sorted(compressed_sizes)
    p25_index = len(ordered_sizes) * 25 / 100.0 + 0.5
    p75_index = len(ordered_sizes) * 75 / 100.0 + 0.5
    p50_index = len(ordered_sizes) * 50 / 100.0 + 0.5

    if p25_index % 1 != 0:
        p25 = (ordered_sizes[int(p25_index) - 1] + ordered_sizes[int(p25_index)]) / 2
    else:
        p25 = ordered_sizes[int(p25_index) - 1]

    if p75_index % 1 != 0:
        p75 = (ordered_sizes[int(p75_index) - 1] + ordered_sizes[int(p75_index)]) / 2
    else:
        p75 = ordered_sizes[int(p75_index) - 1]

    if p50_index % 1 != 0:
        p50 = (ordered_sizes[int(p50_index) - 1] + ordered_sizes[int(p50_index)]) / 2
    else:
        p50 = ordered_sizes[int(p50_index) - 1]

    ipr = p75 - p25

    lower_lim = p50 - 1.5 * ipr
    upper_lim = p50 + 1.5 * ipr

    return lower_lim, upper_lim


# AUXILIARY FUNCTIONS

def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the chunks entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """
    parser.add_argument("-l", "--limits", dest="limits", metavar="METRIC", action="store",
                        help="Metric used to define the upper and lower limits when separating blocks: "
                             "mean_std (mean +/- standard deviation), outliers (P50+/-1.5*IPR) [default: %(default)s]",
                        choices=["mean_std", "outliers"], default="mean_std")
