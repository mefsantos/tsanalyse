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
This module computes the confidence intervals and performs slope analysis of a multiscale dataset.
It parses the csv file to evaluate if it is a dataset resulting from multiscale analysis and extracts the parameters
from the file name.

MODULE EXTERNAL DEPENDENCIES:
numpy(http://numpy.scipy.org/),
pandas(http://pandas.pydata.org/)


ENTRY POINT: HRFAnalyseDirect determines if the input is file or directory to use one of the following entry points.

    (file) confidence_intervals_with_slope_analysis_from_file(input_path, specific_storage=None, sep2read=';',
                                                            sep2write=';', line_term='\n', round_digits=None,
                                                             single_dataset_flag=False, no_slope_analysis_flag=False)

    (directory) confidence_intervals_with_slope_analysis_from_dir(ds_path, sep2read=';', sep2write=';', line_term='\n',
                                                                round_digits=None, single_dataset_flag=False,
                                                                metrics_output_path=None, no_slope_analysis_flag=False)

"""
# TODO: Validate inputs and use DEBUG level from parser

import os
import glob
import pandas

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util


# default multi scale params
START_SCALE = 1
END_SCALE = 20
STEP_SCALE = 1

FILE_SUFFIX = "withConfidenceInterval"
SLOPE_SUFFIX = "withSlopeAnalysis"
HOMEPATH = os.path.abspath(".")

DEBUG = False


def set_multiscale_params(input_path):
    """
    set the parameters used when multiscale was computed
    :param input_path: the path/filename to evaluate and extract the parameters from
    :return:
    """
    START_SCALE, END_SCALE, STEP_SCALE = util.fetch_ms_params(input_path)


# ENTRY POINT FUNCTION
def confidence_intervals_with_slope_analysis_from_file(input_path, specific_storage=None, sep2read=';', sep2write=';',
                                                       line_term='\n', round_digits=None, single_dataset_flag=False,
                                                       no_slope_analysis_flag=False):
    """
    Compute the Confidence Interval and performs slope analysis of the data set in the path given as input
    :param input_path: path of the data set to be read
    :param specific_storage: path to be used to store the csv
    :param sep2read: separator to be considered for the input data set
    :param sep2write: separator to be used in the output data set
    :param line_term: line termination character to be considered. (Unix: '\\n', Posix: '\\r\\n')
    :param round_digits: number of digits to use when applying the round function
    :param single_dataset_flag: activated using parser options to store all the results into a single data set
    :param no_slope_analysis_flag: used to avoid performing slope analysis of the dataset. IF flag is set to True,
    the result will only contain confidence interval metrics
    """
    if util.DEBUG:
        print("DEBUG MODE ::: Active")
        print("no slope flag: %s" % no_slope_analysis_flag)
        print("single dataset: %s" % single_dataset_flag)
        print("round digits: %s" % round_digits)

    # validate input path
    if os.path.exists(input_path):

        csv_file = pandas.read_csv(input_path, sep=sep2read, header="infer")
        if round_digits is not None:
            csv_file = csv_file.round(int(round_digits))

        # to validate the flag for computing mean entropy using directories
        if specific_storage is None:
            if no_slope_analysis_flag:
                storage_path = util.output_name(filename=input_path, filename_suffix=FILE_SUFFIX)
            else:
                storage_path = util.output_name(filename=input_path, filename_suffix=SLOPE_SUFFIX)
        else:
            storage_path = specific_storage

        # I/O Strings Definition
        set_multiscale_params(input_path)

        if not no_slope_analysis_flag:
            # Compute Slope of the multiscales
            csv_file = util.multiscale_least_squares(input_path, csv_file, round_digits=round_digits)

        if util.DEBUG:
            print("test if double_scalar error occurred before this print")

        # Compute the confidence interval
        metrics_df = util.conf_interval(csv_file, string_4_header=None, round_digits=round_digits)

        final_df = pandas.concat([csv_file, metrics_df])
        final_df.to_csv(storage_path, sep=sep2write, index=False, line_terminator=line_term)

        print("Storing file into: %s" % os.path.abspath(storage_path))

        if single_dataset_flag:
            return metrics_df
    else:
        raise Warning("File does not exist!")


# ENTRY POINT FUNCTION
def confidence_intervals_with_slope_analysis_from_dir(ds_path, sep2read=';', sep2write=';', line_term='\n',
                                                      round_digits=None, single_dataset_flag=False,
                                                      metrics_output_path=None, no_slope_analysis_flag=False):
    """
    Compute the Confidence Interval and performs slope analysis of every entry of the data set inside
    the directory given as input.
    :param ds_path: path of the data sets to be evaluated
    :param sep2read: separator to be considered for the input data set
    :param sep2write: separator to be used in the output data set
    :param line_term: line termination character to be considered. (Unix: '\\n', Posix: '\\r\\n')
    :param round_digits: number of digits to keep when rounding numbers. ('None' to avoid rounding)
    :param single_dataset_flag: activated using parser options to store all the results into a single data set
    :param metrics_output_path: used to define the output path for the metrics to be stored. The default path is
    determined based on the input
    :param no_slope_analysis_flag: used to avoid performing slope analysis of the dataset. IF flag is set to True,
    the result will only contain confidence interval metrics
    """

    if os.path.exists(ds_path):

        if no_slope_analysis_flag:
            storage_path = "%s_WithConfidenceInterval" % os.path.abspath(ds_path)
            metrics_dataframe_name = "ConfidenceInterval_dataset_from_%s.csv" % (os.path.basename(ds_path))
        else:
            storage_path = "%s_SlopeAnalysis" % os.path.abspath(ds_path)
            metrics_dataframe_name = "SlopeAnalysis_dataset_from_%s.csv" % (os.path.basename(ds_path))
        if not os.path.exists(storage_path):        # validate/ create storage path
            os.mkdir(storage_path)

        # used when option for dataset with metrics only is activated
        res_df_list, filenames_for_dataframe = [], []


        if metrics_output_path is not None:
            if not os.path.exists(metrics_output_path):
                os.mkdir(metrics_output_path)
            metrics_df_fullpath = os.path.join(metrics_output_path, metrics_dataframe_name)
        else:
            metrics_df_fullpath = os.path.join(HOMEPATH, metrics_dataframe_name)

        ds_list = glob.glob("%s%s*" % (ds_path, os.sep))
        for csv_file in ds_list:                            # iterate over all the csv folders
            if os.path.isfile(csv_file):                    # if it is a file apply transformation
                filename = os.path.split(os.path.abspath(csv_file))[1]
                if no_slope_analysis_flag:
                    output_filename = "%s" % util.output_name(filename, storage_path, FILE_SUFFIX)
                else:
                    output_filename = "%s" % util.output_name(filename, storage_path, SLOPE_SUFFIX)

                res_df = confidence_intervals_with_slope_analysis_from_file(csv_file, specific_storage=output_filename,
                                                                            sep2read=sep2read, sep2write=sep2write,
                                                                            line_term=line_term, round_digits=round_digits,
                                                                            single_dataset_flag=single_dataset_flag,
                                                                            no_slope_analysis_flag=no_slope_analysis_flag)
                if single_dataset_flag:
                    res_df_list.append(res_df)
                    # create a list with the file names to append to the final metrics dataset
                    filenames_for_dataframe.extend([filename] * len(res_df.index))  # repeats the name 4 times

        filenames_df = pandas.DataFrame(filenames_for_dataframe, columns=["Filename"])

        if single_dataset_flag:
            # concat every metric data frame by row
            metrics_df = pandas.concat(res_df_list, axis=0, ignore_index=True)
            metrics_df = metrics_df.rename(columns={'Filename': 'Metrics'})
            # concat the file names df with the metrics_df by column
            output_df = pandas.concat([filenames_df, metrics_df], axis=1)

            output_df.to_csv(metrics_df_fullpath, sep=sep2write, index=False, line_terminator=line_term)
            print("\nStoring file with metrics into: %s" % os.path.abspath(metrics_df_fullpath))
    else:
        raise Warning("Path does not exist!")

# Parser options
def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse parser or subparser,
    and are the optional arguments for the entry function in this module

    """
    # TODO: add parser options to define the input file separator, output file separator and line termination character
    # TODO: add option to define the amount of digits to use when rounding the values
    parser.add_argument("-mo",
                        "--metrics-only",
                        dest="single_dataset",
                        action="store_true",
                        default=False,
                        help="Generate a new dataset containing only the mean, standard deviation and "
                             "confidence intervals computed. Usable with several data sets only; [default: %(default)s]")

    parser.add_argument("-nsa",
                        "--no-slope-analysis",
                        dest="no_slope_analysis",
                        action="store_true",
                        default=False,
                        help="Disables the slope analysis of the dataset. [default: %(default)s]")
