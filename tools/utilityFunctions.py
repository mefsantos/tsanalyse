"""
Copyright (C) 2016 Marcelo Santos

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

This module implements several utility functions to extend python's functionality, enabling verbosity and
 self explanatory code.


MODULE EXTERNAL DEPENDENCIES:
numpy (http://numpy.scipy.org/),
pandas (http://pandas.pydata.org/)
scipy (https://www.scipy.org/)

ENTRY POINT: NONE

"""
# TODO: fix debug flags, adjust debug to comprise levels used in argument parser

import os
import numpy as np
import pandas as pd
import itertools as it
import scipy.stats as st

# HRF package home location - when called by package main scripts, i.e.: TSAnalyse[Direct,MultiScale,...]
TSA_HOME = os.path.abspath(".")
DEBUG_PATH = os.path.join(TSA_HOME, "debug_runs")
RUN_ISOLATED_FILES_PATH = os.path.join(TSA_HOME, "individual_runs")
BLOCK_ANALYSIS_OUTPUT_PATH = os.path.join(TSA_HOME, "block_analysis")
FILE_BLOCKS_STORAGE_PATH = os.path.join(TSA_HOME, "file_blocks")
# Check if the folder required for debug and individual runs exists and create them if necessary


# if not os.path.exists(DEBUG_PATH):
#     os.mkdir(DEBUG_PATH)

if not os.path.exists(RUN_ISOLATED_FILES_PATH):
    os.mkdir(RUN_ISOLATED_FILES_PATH)


# DEBUG FLAG
DEBUG = False


# List utility functions
def head(v_list, num_elements=1):
    """
    Obtain the first 'num_elements' from 'list'
    default value: 1
    :param v_list: list to extract the head from
    :param num_elements: number of elements that compose the head (default = 1)
    :return: the first num_elements
    """
    return v_list[0:num_elements]


def tail(v_list, num_elements=None):
    """
    Obtain the last 'num_elements' from 'v_list'
    default value: length(list) - 1
    :param v_list: input list to obtain the tail from
    :param num_elements: number of elements composing the tail
    :return: last num_elements
    """
    if num_elements is None:
        num_elements = len(v_list)-1
    return v_list[(len(v_list)-num_elements):]


def first(v_list):
    """
    return the first element of a list
    :param v_list: list to extract the first element
    :return: the first element
    """
    return head(v_list, 1)[0]


def rec_first(v_list):
    """
    recursive implementation of first(). useful to extract the first element in nested lists
    :param v_list: list to extract the first element
    :return: the first element
    """
    res = v_list
    if type(v_list) == list:
        return rec_first(first(v_list))
    return res


def last(v_list):
    """
    return the last element of a list
    :param v_list: last to extract the first element
    :return: the last element
    """
    if type(v_list) == list:
        return tail(v_list, 1)[0]
    return v_list


def rec_last(v_list):
    """
    recursive implementation of last(). useful to extract the last element in nested lists
    :param v_list: list to extract the last element
    :return: the last element
    """
    res = v_list
    if type(v_list) == list:
        return rec_last(tail(v_list,1)[0])
    return res


def from_object_to_list(iter_list):
    """
    convert object (Series, etc) into python basic list type
    :param iter_list:
    :return: the converted list
    """
    mlist = list()
    for obj in iter_list:
        mlist.append(obj)
    return mlist


def alternate_merge_lists(fst_list, snd_list):
    """
    merges two lists by alternating elements.
    Ex: [1,2,3] and [4,5,6] = [1,4,2,5,3,6]
    :param fst_list: list to start
    :param snd_list: list to alternate elements with
    :return: alternated list
    """
    iters = [iter(fst_list), iter(snd_list)]
    return list(iter_item.next() for iter_item in it.cycle(iters))


def round_list(l, digits):
    """
    Extends the round(value, ndigits) to a list
    By Skipping strings and characters allows to round lists with mixed types
    Use recursive call to enable rounding nested lists
    Further extended to any "list-alike" object
    If digits == 0, converts to type int
    :param l: list to be rounded
    :param digits: number od decimal cases to consider
    :return: the list with the values rounded to 'ndigits' units
    """
    l = from_object_to_list(l)
    rl = list()
    for v in l:
        if type(v) == list:
            rl.append(round_list(v, digits))
        else:
            if is_number(v):
                if digits == 0:
                    rl.append(int(round(v, digits)))
                else:
                    rl.append(round(v, digits))
            else:
                rl.append(v)
    return rl


def lowercase_list(input_list):
    """
    expands lower() to type list
    :param input_list: list to lowercase
    :return: 'lowered-case' list
    """
    return [word.lower() for word in input_list]


def list_of_lists_with_size(this_list_to_slice, this_size_of_each_list):
    """
    create a list of lists where each list's length will be of 'size_of_each_list'
    :param list_to_slice: the list to slice
    :param size_of_each_list: the size that each list will have
    :return: the list of lists
    """
    lol = lambda this_list_to_slice, this_size_of_each_list: [this_list_to_slice[i:i + this_size_of_each_list]
                                                    for i in range(0, len(this_list_to_slice), this_size_of_each_list)]
    return lol(this_list_to_slice, this_size_of_each_list)


def slice_list_into_lists(input_list, n_lists_to_create):
    """
    create a lists of n lists from 'input_list' based on 'n_lists_to_create'
    :param input_list: list to slice
    :param n_lists_to_create: number of lists to create
    :return: list of lists
    """
    input_size = len(input_list)
    slice_size = input_size / n_lists_to_create
    remain = input_size % n_lists_to_create
    result = []
    iterator = iter(input_list)
    for i in range(n_lists_to_create):
        result.append([])
        for j in range(slice_size):
            result[i].append(iterator.next())
        if remain:
            result[i].append(iterator.next())
            remain -= 1
    return result


def compute_iqr(list_2_eval):
    """
    compute Inter-quartile range from list 'list_2_eval'
    :param list_2_eval:
    :return: the inter-quartile range value
    """
    q75, q25 = np.percentile(list_2_eval, [75, 25])
    return q75 - q25


def pow_with_nan(x, y):
    try:
        return pow(x, y)
    except ValueError:
        return float('nan')


def is_number(v):
    """
    test if the input is numeric
    :param v: argument to evaluate
    :return: True if the input is numeric, False otherwise
    """
    try:
        float(v)
        return True
    except ValueError:
        return False


# Data frames evaluation
def data_frame_has_column(df, col):
    """
    Tests if data frame contains the column 'col'
    :param df: data frame toe valuate
    :param col: column name
    :return: True if column exists, False otherwise
    """
    try:
        df[col]
        return True
    except KeyError:
        return False


# Files and Paths Utility Functions
def remove_file_extension(file_name):
    """
    removes the file extension without being affected by the usage of dots in the file name
    :param file_name: name/file path to be processed
    :return: the name/path of the file without the file extension
    """
    return '.'.join(file_name.split('.')[:-1])


def get_file_extension(file_name):
    if not os.path.isdir(file_name):
        return '.'.join(file_name.split('.')[-1])
    return ""


def remove_slash_from_path(path):
    # type: (object) -> object
    """
    remove the tailing '/' from the path argument
    :param path: path to be processed
    :return: return the processed path without the '/' (one or more) at the end
    """
    if path is not None:
        if path[-1] == "/":
            return remove_slash_from_path(path[:-1])
    return path


def listdir_no_hidden(path):
    """
    List files inside directory omitting the hidden files (starting with '.')
    :param path: path of the directory to list the files from
    :return: the list of files inside the directory
    """
    dir_list = []
    for fl in os.listdir(path):
        if not fl.startswith('.'):
            dir_list.append(fl)
    return dir_list


def generate_header_from_list_with_string(base_list, string_for_header):
    return map(lambda val: ("%s_%s" % (string_for_header, val)), [i for i in range(1, len(base_list))])


def replace_char_in_filename_by(path_to_eval=".", char_to_remove=" ", char_to_place="_"):
    """
    Replace char_to_remove in file names for char_to_replace in a given directory
    :param path_to_eval: path to evaluate
    :param char_to_remove: character to be replaced
    :param char_to_replace: character to be placed instead of space
    """
    dir_path = os.path.expanduser(remove_slash_from_path(path_to_eval))
    if os.path.exists(dir_path):
        if os.path.isdir(dir_path):
            for filename in os.listdir(dir_path):
                new_name = filename.replace(char_to_remove, char_to_place)
                name_2_write = os.path.join(dir_path, filename.replace(" ", char_to_place))
                if new_name != filename:
                    os.rename(os.path.join(dir_path, filename), name_2_write)
                    print("Renaming %s into %s" % (filename, new_name))
    else:
        raise IOError("Path does not exist.")


# dataset name
def get_dataset_name_from_path(dataset_path):
    if os.path.isdir(dataset_path):
        return os.path.basename(dataset_path).replace(" ", "_")
    return (os.path.basename(dataset_path).replace(" ", "_")).replace(".", "_")


def output_name(filename, basepath=None, filename_suffix=""):
    """
    Generate the output filename based on the input name
    :param filename: name of the data set
    :param basepath: path to use as base to generate the output file path.
    If undefined uses previous Absolute path of the file
    :param filename_suffix: the suffix to append to the initial name of the file (default is Empty)
    :return: output name (absolute path) to be used
    """
    file_name = remove_file_extension(filename)
    base_name = os.path.basename(file_name)
    dir_name = os.path.dirname(os.path.abspath(file_name))
    if basepath is None:
        outputname = "%s%s%s_%s.csv" % (dir_name, os.sep, base_name, filename_suffix)
    else:
        outputname = "%s%s%s_%s.csv" % (remove_slash_from_path(basepath), os.sep, base_name, filename_suffix)
    return outputname


# write list to file
def write_list_to_file(file_2_write, list_2_write):
    """
    Write a list into a file
    :param file_2_write: file to write
    :param list_2_write: list to write
    """
    # guarantees the path to the file exists
    parent_dir = os.path.dirname(os.path.abspath(file_2_write))
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    f2w = open(file_2_write,'w')
    for val in list_2_write:
        f2w.write("%d\n" % val)
    f2w.close()


# Multi Scale related
def fetch_ms_params(input_path):
    """
    parse the file name to extract the parameters set for the multiscale operation
    :param input_path: the filename/file path to evaluate
    :return: start, end and step scale parameters
    """
    base_name = os.path.basename(os.path.abspath(input_path))
    if is_multiscale(base_name):
        # discard everything before the word "multiscale" and extract the parameters from the next 3 integers
        str_with_params = tail(base_name.rpartition("multiscale"), 1)[0]
        return parse_ms_params(str_with_params)
    return 0, 0, 0  # if multiscale is not use, the values are irrelevant


# Filename parsers
def parse_ms_params(path):
    """
    parse path for multiscale parameters, returns the start, end and step parameters from the multiscale computation
    :param path: file name to evaluate
    :return: (start, end, step)
    """
    start, end, step = head([int(s) for s in path.split("_") if s.isdigit()], 3)
    return start, end, step


def is_multiscale(string2parse):
    """
    Test if the the datasets were compressed using multiscale
    :param string2parse: dataset name (path)
    :return: Either True if multiscale was used or False otherwise
    """
    return False if (-1 == string2parse.find("multiscale")) else True


# Compression
def compression_ratio(original, compressed, round_digits=4):
    """
    Compute the compression ratio
    :param original: original size of the file
    :param compressed: size of the compressed file
    :param round_digits: amount of decimal cases to consider when rounding the number
    :return: the compression ratio
    """
    if round_digits is None:
        round_digits = 4
    return round(float((float(compressed) / float(original)) * 100), int(round_digits))


# Confidence Interval
def conf_interval(data_frame, conf_percent=0.95, string_4_header=None, round_digits=None):
    """
    Computes the Mean, Std. Deviation and Upper and Lower Confidence Intervals on a given dataset.
    :param data_frame: data set to evaluate
    :param conf_percent: percentage of confidence to use [Default: 0.95]
    :param string_4_header: String to append to the metrics [Default: CR - (Compression Ratio)]
    :param round_digits: number of digits to use when applying round
    :return: a data frame containing the mean, standard deviation and the confidence interval
    """
    if string_4_header is None:
        string_4_header = ""
    res_list = list()
    df_mean = ["Mean%s" % string_4_header]
    df_std = ["SDev%s" % string_4_header]
    df_ci_min = ["LowerCInterval%s" % string_4_header]
    df_ci_max = ["UpperCInterval%s" % string_4_header]
    for i in range(1, len(data_frame.keys())):

        df_col = np.array(data_frame.ix[:, i])
        col_mean = np.mean(df_col)
        col_std = np.std(df_col)
        ci_min, ci_max = st.t.interval(conf_percent, len(df_col)-1, loc=col_mean, scale=st.sem(df_col))
        df_mean.append(col_mean)
        df_std.append(col_std)
        df_ci_min.append(ci_min)
        df_ci_max.append(ci_max)

        # print("df_mean: %s\n df_stdev: %s, ")

    res_list.append(df_mean)
    res_list.append(df_std)
    res_list.append(df_ci_min)
    res_list.append(df_ci_max)

    if round_digits is not None:
        res_list = round_list(res_list,int(round_digits))

    return pd.DataFrame(res_list, columns=data_frame.keys())


# Least Squares Regression
def multiscale_least_squares(df_name, data_frame, round_digits=None):
    """
    Compute the slope of each row entry of the dataset using least squares regression.
    If the dataset has multiscales to evaluate appends the resulting slopes to the original dataset and return
    the concatenated data sets. Raises Warning otherwise
    :param df_name: name/path of the data set
    :param data_frame: data frame to evaluate
    :param round_digits: number of decimals to use when rounding the values [Default: None]
    :return: the resulting data set if successfully evaluated
    """
    # TODO: adjust the iteration cycle to use a specific stop point to compute the slope [currently: len(all_y_values)]
    # TODO: validate inputs (dataset, etc)
    
    if is_multiscale(df_name):
        start, end, step = parse_ms_params(df_name)
        data_frame_slopes = list()  # store the slope array of each row
        all_x_values = range(start, end+1, step)
        for df_line in data_frame.iterrows():
            slopes_per_row = list()  # store the slopes for one row
            slopes_df_header = list()  # header of the data frame to concatenate with the original
            row_values = np.array(df_line[1].ix[1:])  # all the values of each row
            if DEBUG:
                print("Header, Slope, x[i], y[i]")
            for i in range(2, len(all_x_values)+1):  # iterate over the number os slopes to compute
                y_array = list(row_values[0:i])
                x_array = all_x_values[0:i]
                iter_to_header = "Slope_%d:%d" % (start, all_x_values[i-1])
                slope = compute_least_squares(x_array=x_array, y_array=y_array, round_digits=round_digits)
                slopes_per_row.append(slope)
                if DEBUG:
                    print("%s, %.4f, %s, %s" % (iter_to_header, slope, x_array, y_array))
                slopes_df_header.append(iter_to_header)
            # gather every slopes_per_row in a nested list (of lists)
            data_frame_slopes.append(slopes_per_row)
        # create new data frame
        slopes_data_frame = pd.DataFrame(data_frame_slopes, index=None, columns=slopes_df_header)
        # merge all data frames
        result_df = pd.concat([data_frame, slopes_data_frame], axis=1)
        return result_df
    else:
        raise Warning("Dataset is not in multiscale format")


def compute_least_squares(x_array, y_array, round_digits=None):
    """
    Uses least squares regression to compute the slope of the input data
    :param x_array: x values
    :param y_array: y values
    :param round_digits: number of decimals to round to [Default: None]
    :return: the slope computed
    """
    slope, intercept, r_value, p_value, std_err = st.linregress(x_array,y_array)
    if round_digits is None:
        return slope
    return round(slope, round_digits)


# Parse arguments validation
def path_exists(dataset_path):
    if not os.path.exists(dataset_path):
        raise os.FileNotFound  # or TypeError, or `argparse.ArgumentTypeError
    return dataset_path


# TODO: use existing debug-level to activate debug mode and debug directory
# STDIN parser
# Common parser options when dealing with csv files
def add_csv_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse parser or subparser,
    and are the optional arguments for the invoked modules
    """
    parser.add_argument("-o",
                        "--output-path",
                        dest="output_path",
                        action="store",
                        help="Specifies the path to save the resulting data set containing the metrics "
                             "to isolate from the input data sets; [default:%(default)s]")

    parser.add_argument("-insep",
                        "--read-separator",
                        dest="read_separator",
                        action="store",
                        default=";",
                        help="Specifies the csv separator character to use in the given input; [default:'%(default)s']")

    parser.add_argument("-outsep",
                        "--write-separator",
                        dest="write_separator",
                        action="store",
                        default=";",
                        help="Specifies the csv separator character to use in the output files; [default:'%(default)s']")

    parser.add_argument("-lineterm",
                        "--line-terminator",
                        dest="line_terminator",
                        action="store",
                        default="\n",
                        help="Specifies the character to use as line termination; [default:'\\n']")


def add_numbers_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse parser or subparser,
    and are the optional arguments for the invoked modules
    """
    parser.add_argument("-round",
                        "--round-digits",
                        dest="round_digits",
                        action="store",
                        help="Specifies number of digits to use when rounding values; [default: %(default)s]")
