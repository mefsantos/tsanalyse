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
import pandas as pd

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util


def duration_in_seconds_for_list_with_sampling_frequency(list_of_values, sampling_frequency=2):
    duration = len(list_of_values) / float(sampling_frequency)
    return duration


def compute_duration_from_file(file_path, sampling_frequency_hz=2):
    csv_record = pd.read_csv(os.path.abspath(file_path))
    values_list = list(csv_record.ix[:, 0])
    return duration_in_seconds_for_list_with_sampling_frequency(list_of_values=values_list, sampling_frequency=sampling_frequency_hz)


def compute_duration_from_dirs(data_set_path, sampling_frequency_hz=2):

    directories_list = util.listdir_no_hidden(data_set_path)
    for directory in directories_list:
        duration_of_dir = list()
        dir_name = os.path.basename(os.path.abspath(directory))
        dir_path = os.path.join(data_set_path, directory)
        file_names = list()
        directory_files = util.listdir_no_hidden(dir_path)
        duration_of_files = list()
        for ds_file in directory_files:
            file_name = os.path.join(dir_path, ds_file)
            file_names.append(ds_file)
            # print("File to read %s. filename: %s" % (file_name, ds_file))
            duration_of_files.append(compute_duration_from_file(file_name,
                                                                sampling_frequency_hz=sampling_frequency_hz))
        duration_of_dir.append(file_names)
        duration_of_dir.append(duration_of_files)

        ds_dir_duration_out_name = os.path.join(os.path.dirname(os.path.abspath(util.remove_slash_from_path(data_set_path))),
                                                "%s.csv" % dir_name)

        dir_data_frame = pd.DataFrame(duration_of_dir)
        dir_data_frame = dir_data_frame.transpose()
        dir_data_frame.columns = ["Filename", "Duration(s)"]

        dir_data_frame.to_csv(ds_dir_duration_out_name, sep=";", index=False)
        print("Storing file in %s" % ds_dir_duration_out_name)
    return None
