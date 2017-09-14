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
This module enables the conversion of csv files to a specific format to provide to SisPorto software (TxSP3)

MODULE EXTERNAL DEPENDENCIES:
numpy(http://numpy.scipy.org/),
pandas(http://pandas.pydata.org/)

ENTRY POINT:

    parse_input_path(ds_path, ua_value=0, sep2read='\s+', sep2write='\t', line_term = '\r\n')

"""

import os
import glob
import numpy
import pandas

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util

HOMEPATH = os.path.abspath(".")

# validate/create output path for sisporto formatted files
SISPORTO_PATH = os.path.join(HOMEPATH, "sisporto_txsp3")

if not os.path.exists(SISPORTO_PATH):
    os.mkdir(SISPORTO_PATH)

# SISPORTO FILE HEADERS
SISPORTO_HEADER1 = "SISPORTO EXPORT FILE"
SISPORTO_HEADER2 = "VER:00005"
SISPORTO_COLUMN_HEADER = "DT FHR UC FM FMA FMB FHRTYPE UCTYPE\n"
# NOTE:
# (units in integer/long values)
# (multiplying values by 1000 should be enough)


def csv_2_txsp3(input_path, storage_path=SISPORTO_PATH, ua_value=0, sep2read='\s+', sep2write=' ', line_term='\n'):
    """
    receive a path of a single csv file to reformat to be sisporto compatible
    :param input_path: fullpath for the input csv file
    :param storage_path: path to store the txsp3 file
    :param ua_value: value to be used for the UA array
    :param sep2read: input file separator
    :param sep2write: output file separator [default:'\s']
    :param line_term: line terminator [default:'\s']
    :return: NULL
    """
    header_fields = ["time", "bpm"]

    csv_record = pandas.read_csv(input_path, sep=sep2read, names=header_fields)

    # DT definition
    time_array = csv_record["time"]
    time_array = util.tail(time_array)  # remove the header
    # cast to double to compute time differences, multiply by 1000 and cast to int to remove decimal character (.0)
    dt_sisporto = (numpy.diff(numpy.array(time_array).astype(float)) * 1000).astype(int)
    # append a value equal to the first time difference to match the fhr_array length
    dt_sisporto = numpy.append(dt_sisporto, util.head(dt_sisporto))

    # FHR definition
    fhr_array = csv_record["bpm"]
    fhr_array = util.tail(fhr_array)  # remove the header
    # cast from string to float, multiply by 1000 and cast to int
    fhr_sisporto = (numpy.array(fhr_array).astype(float) * 1000).astype(int)

    # UA definition
    uc_sisporto = [ua_value] * len(dt_sisporto)
    # remaining fields - FM FMA FMB FHRTYPE UCTYPE
    remaining_arrays_sisporto = [0] * len(dt_sisporto)

    # output name and path definition
    parent_dir, file_name = os.path.split(os.path.abspath(input_path))
    name2use, file_termination = os.path.splitext(file_name)
    output_name = os.path.join(storage_path,  "%s.TxSP3" % name2use)

    # txsp3 file generation and storage
    sisporto_df = pandas.DataFrame()
    sisporto_df["DT"] = dt_sisporto
    sisporto_df["FHR"] = fhr_sisporto
    sisporto_df["UC"] = uc_sisporto
    sisporto_df["FM"] = remaining_arrays_sisporto
    sisporto_df["FMA"] = remaining_arrays_sisporto
    sisporto_df["FMB"] = remaining_arrays_sisporto
    sisporto_df["FHRTYPE"] = remaining_arrays_sisporto
    sisporto_df["UCTYPE"] = remaining_arrays_sisporto

    with open(output_name, 'w') as file2write:
        file2write.write("%s%s" % (SISPORTO_HEADER1, line_term))
        file2write.write("%s%s" % (SISPORTO_HEADER2, line_term))

        sisporto_df.to_csv(file2write, sep=sep2write, index=False, line_terminator=line_term)

    print("Storing file into: " + output_name)


# TODO: add option from main package to determine the OS type separator - \r\n for posix and \n for unix
# TODO: use parser options from the csv argument parser (utilityFunctions.py)
# ENTRY POINT FUNCTION
def parse_input_path(ds_path, ua_value=0, sep2read='\s+', sep2write='\t', line_term ='\r\n'):
    """
    Receive a path for several data sets and convert the csv data sets into TxSP3 format
    :param ds_path: fullpath for the datasets
    :param ua_value: value to use as UA
    :param sep2read: input file separator  [default:'\s+']
    :param sep2write: output file separator [default:'\t']
    :param line_term: line termination character [default (adjusted for windows):'\r\n']
    :return: NULL
    """

    ds_list = glob.glob(ds_path+os.sep+"*")
    for dataset in ds_list:         # iterate over all the data sets folders
        if os.path.isdir(dataset):  # if it is a directory open and save the name to use as storage_path
            parent_path, dataset_name = os.path.split(dataset)
            storage_path = os.path.join(SISPORTO_PATH, "%s" % dataset_name)
            if not os.path.exists(storage_path):  # validate/ create storage path
                os.mkdir(storage_path)
            dataset_files = glob.glob(dataset+os.sep+"*")
            for ds_file in dataset_files:    # iterate over all the files of a dataset
                if os.path.isfile(ds_file):  # if it is a file apply transformation
                    csv_2_txsp3(ds_file, storage_path, ua_value=ua_value, sep2read=sep2read,
                                sep2write=sep2write, line_term=line_term)
