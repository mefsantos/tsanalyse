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

This module computes the duration of each record from every file contained in the input directory


MODULE EXTERNAL DEPENDENCIES:
pandas(http://pandas.pydata.org/)

ENTRY POINT:

    parse_input_path(input_path, output_location=HOMEPATH)

"""

import os
import glob
import pandas

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util


HOMEPATH = os.path.abspath("..")  # used if no output_dir is provided
# should be something like: /path/to/package/hrfanalyse-master


def calculate_duration(inputdir, storage_path=HOMEPATH, sep2read='\s+', sep2write=';', all_in_one=False):
    """
    Compute duration of each recording of each file contained in the folder located in input path
    stores the file name and the recording duration of the data set in a file in the parent directory
    File name: dataset_filename.csv. ex: ./Grupo_MA_S0001312.TxSP3.csv
    :param inputdir: directory of the data set (recording files)
    :param storage_path: directory where the resulting csv file will be stored. Uses HOMEPATH if None is provided
    :param sep2read: separator used in the csv file to be read
    :param sep2write: separator to use in the csv file to write
    :param all_in_one: flag to gather all the metrics into a single dataset
    """
    time_secs, time_mins, names = [], [], []
    ds_owner_name = os.path.basename(os.path.dirname(os.path.abspath(inputdir)))
    header_fields = ["time", "bpm"]
    fileslist = util.listdir_no_hidden(inputdir)
    print(inputdir)

    for csv_path in fileslist:

        csv_record = pandas.read_csv(inputdir + os.sep + csv_path, sep=sep2read, names=header_fields)

        time_array = list(csv_record["time"])
        rec_duration = float(util.tail(time_array, 1)[0]) - float(util.head(time_array,2)[1])

        time_secs.append(rec_duration)
        time_mins.append(round(rec_duration/60, 2))

        names.append(csv_path)

    dir_name = os.path.basename(os.path.abspath(inputdir))
    storage_location = os.path.join(storage_path, "%s_duration" % ds_owner_name)
    if not os.path.exists(storage_location):
        os.mkdir(storage_location)
    output_name = os.path.join(storage_location, "%s.csv" % dir_name)

    recs_df = pandas.DataFrame()
    recs_df["file_name"] = names
    recs_df["recs_duration_secs"] = time_secs
    recs_df["recs_duration_mins"] = time_mins

    if all_in_one:  # return the group and the resulting data frame
        return os.path.split(inputdir)[1], recs_df
    else:           # otherwise writes the dataset
        print("Storing file into: " + output_name)
        recs_df.to_csv(output_name, sep=sep2write, index=False)


# TODO: add parser options from csv argument parser. Validate input
# TODO: finish implementation to add option to gather all in one adding a group column
# ENTRY POINT FUNCTION
def parse_input_path(input_path, output_location=HOMEPATH, sep2read='\s+', sep2write=';', all_in_one=False):
    """
    Entry point for calculate_duration function.
    :param input_path: path to evaluate
    :param output_location: location to store the resulting data sets
    :param sep2read: separator to use for the input data sets
    :param sep2write: separator to use when writing the resulting dataset
    """
    ds_list = glob.glob(os.path.join(input_path, "*"))

    for dataset_path in ds_list:
        calculate_duration(dataset_path, output_location, sep2read=sep2read,
                                           sep2write=sep2write, all_in_one=all_in_one)

def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse parser or subparser,
    and are the optional arguments for the invoked modules
    """
    parser.add_argument("-aio",
                        "--all-in-one",
                        dest="compute_all",
                        action="store_true",
                        default=False,
                        help="Store every data set evaluated into a single dataset; [default:%(default)s]")
