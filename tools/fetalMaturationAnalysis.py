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
This module implements an analysis on a specific dataset. Specifically enables creating nested groups to evaluate
its entropy and compression.
Example: ./HRFAnalyseDirect.py individual_testing_files/baselongitudinal.csv longitbase -insep ","
Note: -insep flag is required due to the dataset original type

MODULE EXTERNAL DEPENDENCIES:
pandas(http://pandas.pydata.org/)
numpy(http://numpy.scipy.org/)

ENTRY POINT:

    longit_base_analysis(input_path, sep2read=",", sep2write=";", line_term="\n", num_of_columns_to_keep=12,
                         round_digits=None, specific_storage=None, debug_flag=False, debug_level=0, encoding="latin_1",
                         group_by="semana", number_of_groups=4)

"""

import os
import math as m
import pandas as pd

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util


# TODO: use debug flags from argument parser (INFO, WARNING, etc)
# HOME
HRF_HOME = os.path.abspath(".")
# Encoding (necessary in this dataset)
ENCODING = "latin_1"

DEBUG_LEVEL = 0

if DEBUG_LEVEL >=1:
    debug_path = "/home/msantos/Desktop/CINTESIS/Rotinas/hrfanalyse-master/individual_testing_files/baselongitudinal.csv"
    data_frame = pd.read_csv(debug_path, sep=",")


# TODO: dynamic group generation based on the number of groups desired
def create_groups():
    wg = list()
    wg.append(range(24, 29))
    wg.append(range(29, 33))
    wg.append(range(33, 37))
    wg.append(range(37, 41))
    return wg


def dynamic_groups(col_2_group_by, n_groups):
    """
    Dynamically generates the groups based on the paramaters provided
    :param col_2_group_by: column to use as grouping factor
    :param n_groups: number of groups to generate
    :return: a list containing the groups generated
    """
    # TODO: fix problem regarding the division remainder - in which group to place the remaining entries
    list_2_gen_group = sorted(col_2_group_by.unique())
    l_min = min(list_2_gen_group)
    l_max = max(list_2_gen_group)
    elems_per_group = (l_max - l_min + 1) / float(n_groups)
    if DEBUG_LEVEL >= 2:
        print("unique sorted column list: %s" % list_2_gen_group)    
        print("Min: %d,max: %d, n_elems_per_group: %d" % (l_min, l_max, elems_per_group))
    groups_list = list()
    if elems_per_group.is_integer():
        print("is integer")
        elems_per_group = int(elems_per_group)
        # make group directly from list
        for i in range(l_min, l_max, elems_per_group):
            groups_list.append(range(i, i+elems_per_group))
    else:
        print("is float")
        # first group has one more element
        fst_max = l_min + int(m.ceil(elems_per_group))
        groups_list.append(range(l_min, fst_max))
        # redefine start and step
        step = int(m.floor(elems_per_group))
        # start and the last element read +1
        new_start = fst_max # python range goes to i-1
        print("first max: %d, first list: %s\nnew start: %d, step: %d"
        % (fst_max, groups_list, new_start, step ))
        # append the remaining groups
        for i in range(new_start, l_max, step):
            groups_list.append(range(i, i+step))
    return groups_list


# TODO: change to receive debug-level only
def set_debug_and_encoding(debug_flag, debug_level, encoding):
    """
    Sets the debug mode, level and encoding
    :param debug_flag: debug flag
    :param debug_level: debug level
    :param encoding: encoding type
    :return:
    """
    util.DEBUG=debug_flag
    DEBUG_LEVEL=debug_level
    ENCODING=encoding


def get_df_column_group_name(gps, group_id):
    """
    Creates label that represent the groups created
    :param gps: groups to generate the label
    :param group_id: id of the group to generate the string
    :return: label of the group
    """
    group = gps[group_id]
    group_name = "Group_%d:%d" % (util.first(group), util.last(group))
    return group_name


def group_data_frame_by(data_frame, group_argument="semana", cols_2_keep=12):
    """
    Generates a list of data frame each grouped by the values of the 'group_argument' column
    :param data_frame:  data frame to group
    :param group_argument: column to group by
    :param cols_2_keep: number of columns to keep when discarding irrelevant data
    :return: list of data frames grouped by column values
    """
    data_frames_list = list()
    groups = create_groups()
    if DEBUG_LEVEL >= 4:
        print("\n\n ::: DATA SETS ::: \n\n")
    for group in groups:
        df_grouped_by = data_frame[data_frame[group_argument].isin(group)]
        # keep the earlier week in duplicate entries
        processed_data_frame = df_grouped_by.drop_duplicates(subset="sujeito", keep="first")
        # remove unnecessary columns
        processed_data_frame = select_columns_to_evaluate(processed_data_frame, num_of_columns_to_keep=cols_2_keep)
        if DEBUG_LEVEL >= 4:
            print("\n\n Processed df columns: %s" % processed_data_frame.keys())
            print(processed_data_frame)
        data_frames_list.append(processed_data_frame)

    if DEBUG_LEVEL >= 2:
        print("Number of data sets: %d" % len(data_frames_list))
    return data_frames_list


def select_columns_to_evaluate(data_frame, num_of_columns_to_keep=12, keep_until_column=None):
    """
    Discard irrelevant columns from the dataset based on provided parameters
    :param data_frame: data frame to process
    :param num_of_columns_to_keep: number of columns to keep (starting at the first column)
    :param keep_until_column: name of the last column to keep (not working yet)
    :return: the processed data frame
    """
    # TODO: cut by column name. until then, it will be cut by number of columns
    # keep the first N-columns to compute the metrics the first columns until a specific column name is found: ex: normal
    # if keep_until_column is None:
    res_data_frame = data_frame.ix[:, 0:int(num_of_columns_to_keep)]
    return res_data_frame


def compute_metrics_to_data_frame(data_frame, groups, group_id, round_digits):
    """
    compute the confidence interval metrics from each column of the data frame
    :param data_frame: data frame to evaluate
    :param groups: a list of groups, i.e, a list with the range of values that will generate the groups
    :param group_id: id of the group being evaluated
    :param round_digits: number of digits to use when rounding
    :return: data frame with all the metrics
    """
    # remove first 4 columns (sujeito, semana, filename and originalsize)
    data_frame = data_frame.ix[:, 4:]
    if DEBUG_LEVEL >= 3:
        print("\n GROUP NAME: %s " % get_df_column_group_name(groups, group_id))
        print("\n\n ::: METRICS DATA SET for GROUP %d ::: \n\n " % group_id)
        
    header_of_df = ["Group"]
    values_2_df = [get_df_column_group_name(groups, group_id)]
    for column_header in data_frame.keys():
        # send the column duplicated due to conf_interval implementation
        df_with_metrics = (util.conf_interval(data_frame=pd.DataFrame(data_frame[[column_header, column_header]]),
                                              string_4_header="_%s" % column_header, round_digits=round_digits)).transpose()

        values_2_df.extend(util.from_object_to_list(df_with_metrics.ix[1, :]))           
        header_of_df.extend(util.from_object_to_list(df_with_metrics.ix[0, :]))

    if DEBUG_LEVEL >=3:
        print("\n\n header: %s" % header_of_df)
        print("\n\n values: %s" % values_2_df)

    res_data_frame = pd.DataFrame([values_2_df], columns=header_of_df)
    if DEBUG_LEVEL >= 3:
        print(res_data_frame)

    return res_data_frame


def process_data_frames_list(data_frames_list, round_digits):
    """
    Processes a list of data frames to compute the metrics from each and returns a single data frame
     with all the metrics computed
    :param data_frames_list: list of data frames to process
    :param round_digits: number of digits to use when rounding
    :return: final data frame
    """
    resulting_df_list = list()
    groups = create_groups()
    group_id = 0
    for df_to_process in data_frames_list:
        df_with_metrics = compute_metrics_to_data_frame(df_to_process, groups, group_id, round_digits)
        resulting_df_list.append(df_with_metrics)
        group_id += 1
    final_df = pd.concat(resulting_df_list, ignore_index=True, axis=0)
    return final_df


# ENTRY POINT FUNCTION
def fetal_maturation_analysis(input_path, sep2read=",", sep2write=";", line_term="\n", num_of_columns_to_keep=12,
                              round_digits=None, specific_storage=None, debug_flag=False, debug_level=0, encoding="latin_1",
                              group_by="semana", number_of_groups=4):
    """
    evaluates longitudinal base dataset to compute confidence interval metrics.
    Divides the data set into several groups defined with the parameters provided, discard the irrelevant data, and
     computes the aforementioned metrics.
     (so far) also generates (hardcoded) two additional data sets divided by 'part_pre-termo' values [0,1]
    :param input_path: path to read the file from
    :param sep2read: separator used when reading from the dataset
    :param sep2write:separator used when writing the result data set
    :param line_term: line terminator character used when reading and writing the data set
    :param num_of_columns_to_keep: number of columns to keep when discarding irrelevant data
    :param round_digits: number of digits to use when rounding data
    :param specific_storage: name of the output file (optional)
    :param debug_flag: flag to activate the debug mode
    :param debug_level: level of debugging to use
    :param encoding: encoding used in the input data set
    :param group_by: column of the input data set to generate the groups
    :param number_of_groups: number of groups to be created
    :return:
    """

    set_debug_and_encoding(debug_flag, debug_level, encoding)
    data_frame = pd.read_csv(input_path, sep2read)

    # hardcode a refazer - divide em 2 grupos:
    # TODO: merge data frames (remove first column from the second)
    df_pretermo_0 = data_frame[data_frame["part_pre_termo"].isin(["0"])]
    df_pretermo_1 = data_frame[data_frame["part_pre_termo"].isin(["1"])]

    # validate string to group the data
    if util.data_frame_has_column(data_frame, group_by):

        data_frames_list = group_data_frame_by(data_frame, group_by)
        data_frames_list_pt_0 = group_data_frame_by(df_pretermo_0, group_by)
        data_frames_list_pt_1 = group_data_frame_by(df_pretermo_1, group_by)

        final_df = process_data_frames_list(data_frames_list, round_digits)
        final_df_pt_0 = process_data_frames_list(data_frames_list_pt_0, round_digits)
        final_df_pt_1 = process_data_frames_list(data_frames_list_pt_1, round_digits)

        storage_path = os.path.join(HRF_HOME, "LongitBaseAnalysis.csv")
        storage_path_pt_0 = os.path.join(HRF_HOME, "LongitBaseAnalysis_pre-term_0.csv")
        storage_path_pt_1 = os.path.join(HRF_HOME, "LongitBaseAnalysis_pre-term_1.csv")
        if specific_storage is not None:
            if os.path.exists(os.split(specific_storage)[0]):
                storage_path = specific_storage
                storage_path_pt_0 = os.path.join(os.path.split(specific_storage[0]), "LongitBaseAnalysis_pre-term_0.csv")
                storage_path_pt_1 = os.path.join(os.path.split(specific_storage[0]), "LongitBaseAnalysis_pre-term_1.csv")
            else:
                raise Warning("Path does not exist. Using Default:"
                              "\n General Analysis: %s \n Pre-term 0: %s \n Pre-term 1: %s" %
                              (storage_path, storage_path_pt_0, storage_path_pt_1))

        print("Storing dataset into: %s" % storage_path)
        final_df.to_csv(storage_path, sep=sep2write, index=False, line_terminator=line_term)
        print("Storing dataset into: %s" % storage_path_pt_0)
        final_df_pt_0.to_csv(storage_path_pt_0, sep=sep2write, index=False, line_terminator=line_term)
        print("Storing dataset into: %s" % storage_path_pt_1)
        final_df_pt_1.to_csv(storage_path_pt_1, sep=sep2write, index=False, line_terminator=line_term)

    else:
        raise Warning("Data set does not contain the column provided.\n Please specify an existing column.")


def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse parser or subparser,
    and are the optional arguments for the invoked modules
    """
    parser.add_argument("-c2k",
                        "--columns-to-keep",
                        dest="cols_2_keep",
                        action="store",
                        default=12,
                        help="Specifies the number of columns to keep; [default:'%(default)s']")

    parser.add_argument("-g",
                        "--group-by",
                        dest="group_by",
                        action="store",
                        default="semana",
                        help="Specifies the column to generate the groups; [default:'%(default)s']")

    parser.add_argument("-ngps",
                        "--number-of-groups",
                        dest="number_of_groups",
                        action="store",
                        default=4,
                        help="Specifies number of groups to create; [default:'%(default)s']")

    parser.add_argument("-e",
                        "--encoding",
                        dest="encoding",
                        action="store",
                        default="latin_1",
                        help="Specifies the encoding of the dataset; [default:'%(default)s']")

