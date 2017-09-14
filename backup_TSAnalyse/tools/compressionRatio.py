"""
Copyright (C) 2016 Marcelo Santos

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
This module computes the compression ratio and confidence intervals of data sets obtained from the multi scale analysis.
The path provided as input is parsed to determine the multi scale parameters and the resulting metrics are appended
to the original data sets which are stored with a different name.

MODULE EXTERNAL DEPENDENCIES:
numpy(http://numpy.scipy.org/),
pandas(http://pandas.pydata.org/)

ENTRY POINT:
(file) compression_ratio_from_file(input_path, specific_storage=None, sep2read=';', sep2write=';',
                                line_term='\n', round_digits=2)


(directory) compression_ratio_from_dir(ds_path, sep2read=';', sep2write=';', line_term='\n', round_digits=2)

"""


# TODO: validate inputs from the functions and use default values from the arguments parser

import pandas
import os
import glob
import numpy
try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util


# DEBUG Variables
# debug_dir = "/home/msantos/Desktop/CINTESIS/Rotinas/Datasets/test_ms_cr"
# debug_file = "/home/msantos/Desktop/CINTESIS/Rotinas/Datasets/test_ms_cr/MSA_clean_multiscale_1_20_1_paq8l8.csv"

HOMEPATH = os.path.abspath(".")

# default multiscale params
START_SCALE = 1
END_SCALE = 20
STEP_SCALE = 1
FILE_SUFFIX = "compressionRatio"
# if multiscale evaluate the start, end and step scales
# otherwise use standard start = 1 and end = 20, and step = 1


def set_multiscale_params(input_path):
    """
    set the parameters used when multiscale was computed
    :param input_path: the path/filename to evaluate and extract the parameters from
    :return:
    """
    START_SCALE, END_SCALE, STEP_SCALE = util.fetch_ms_params(input_path)


def make_final_header(filename):
    """
    Generate the Header of the csv to be written.
    If multiscale is detected the header will contain "Compression Rate" for each scale (MS_i_CRx100)
    Otherwise the header will contain the a single "Compression Rate" entry (CRx100)
    :param filename: input file name
    :return: the header to be used
    """
    final_header = ["Filename"]
    if util.is_multiscale(filename):
        for val in range(START_SCALE, END_SCALE+1, STEP_SCALE):
            final_header.append("MS_%d_CRx100" % val)
    else:
        final_header.append("CRx100")
    return final_header


# ENTRY POINT FUNCTION
def compression_ratio_from_file(input_path, specific_storage=None, sep2read=';', sep2write=';', line_term='\n',
                                round_digits=2):
    """
    Compute the Compression Rate of every entry of the data set given.
    if specific storage is provided it will be used, otherwise the output path for the final csv will be determined
    based on the input path
    :param input_path: path of the data set to be read
    :param specific_storage: path to be used to store the csv
    :param sep2read: separator to be considered for the input data set
    :param sep2write: separator to be used in the output data set
    :param line_term: line termination character to be considered. (Unix: "\n", Posix: "\r\n")
    :param round_digits: the number of decimal digits to use when rounding the numbers. 'None' will avoid rounding
    :return:
    """
    csv_file = pandas.read_csv(input_path, sep=sep2read, header="infer")

    # to validate the flag for computing CR over directories
    if specific_storage is None:
        storage_path = util.output_name(filename=input_path, filename_suffix=FILE_SUFFIX)
    else:
        storage_path = specific_storage

    # I/O Strings Definition
    final_header = make_final_header(input_path)
    set_multiscale_params(input_path)
    # create a list of lists . the data set is generated at the end
    final_dataset = list()

    for csv_line in csv_file.iterrows():                        # iterate over the csv file
        line_name = numpy.array(csv_line[1])[0]                 # save line header only - filename
        line_values = util.tail(numpy.array(csv_line[1]))       # save line values only - filename

        result_line = list()
        result_line.append(line_name)                           # start a list to append the results

        for i in range(0,len(line_values),2):                   # iterate over a line
            original, compressed = line_values[i], line_values[i+1]
            comp_rate = util.compression_ratio(original, compressed)
            if round_digits is not None:
                result_line.append(round(comp_rate, round_digits))
            else:
                result_line.append(comp_rate)

        final_dataset.append(result_line)

    temp_df = pandas.DataFrame(final_dataset, columns=final_header)

    # compute mean, stdev and confidence interval (using default confidence value of 95%)
    metrics_df = util.conf_interval(data_frame=temp_df, round_digits=round_digits)
    final_df = pandas.concat([temp_df, metrics_df])

    final_df.to_csv(storage_path, sep=sep2write, index=False, line_terminator=line_term)

    print("Storing file into: " + os.path.abspath(storage_path))


# ENTRY POINT FUNCTION
def compression_ratio_from_dir(ds_path, sep2read=';', sep2write=';', line_term='\n', round_digits=2):
    """
    Compute the compression ratio and confidence intervals of every entry of the data set contained
     in the path given as input.
    :param ds_path: path of the data sets to be evaluated
    :param sep2read: separator to be considered for the input data set
    :param sep2write: separator to be used in the output data set
    :param line_term: line termination character to be considered. (Unix: "\n", Posix: "\r\n")
    :param round_digits: number of decimal units to use when rounding (Default: 2)
    :return:
    """
    storage_path = "%s_CompressionRatio" % os.path.abspath(ds_path)
    if not os.path.exists(storage_path):        # validate/ create storage path
        os.mkdir(storage_path)

    ds_list = glob.glob("%s%s*" % (ds_path, os.sep))

    for csv_file in ds_list:                            # iterate over all the csv folders
        if os.path.isfile(csv_file):                    # if it is a file apply transformation
            filename = os.path.split(os.path.abspath(csv_file))[1]
            output_filename = "%s" % util.output_name(filename, storage_path, FILE_SUFFIX)
            compression_ratio_from_file(csv_file, specific_storage=output_filename, sep2read=sep2read,
                                        sep2write=sep2write, line_term=line_term, round_digits=round_digits)
