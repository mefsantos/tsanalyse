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
This module implements an evaluation to data sets regarding clinical procedures resorting to temporary vessel occlusion.
(clamp).
The implementation consists of dividing the input data set by state. Each state represents a different stage
in the surgery.
0 -> the machine is off;
1 -> the machine started to work but the heart is still beating (comprises the clampage period)
2 -> the machine is on and the heart stopped beating hence the heart rate frequency is 0
3 -> the machine is still working but the heart started beating again to turn off the machine
4 -> machine is off and the heart is beating normally


MODULE EXTERNAL DEPENDENCIES:
pyeeg(http://code.google.com/p/pyeeg/downloads/list),
pandas(http://pandas.pydata.org/)
numpy(http://numpy.scipy.org/),
lzma and brotli python modules
ppmd, paq8l (source files contained in the package under ./algo)

ENTRY POINT: HRFAnalyseDirect evaluates if the input path corresponds to a single file or a directory

    (file) analyse_bvp_by_state_from_file(input_path, entropy_2_use, entropy_tolerance, entropy_dimension,
                                             compressor_2_use, compressor_level, with_compression_ratio=True,
                                            sep2read=";", sep2write=";", line_term="\n",
                                            store_by_state=True, output_path=None, compute_all=False)

    (directory) analyse_bvp_by_state_from_dir(input_path, entropy_2_use, entropy_tolerance, entropy_dimension,
                                            compressor_2_use, compressor_level, with_compression_ratio=True,
                                            sep2read=";", sep2write=";", line_term="\n", store_by_state=True,
                                            output_path=None, compute_all=False)

"""
import os
import sys
import glob
import numpy as np
import pandas as pd

try:
    import tools.pyeeg as pyeeg
except ImportError:
    import pyeeg as pyeeg

try:
    import tools.compress as comp
except ImportError:
    import  compress as comp

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util

# default "Home" for bvp analysis
BVP_HOME = os.path.join(os.path.abspath("."), "clampage_state_analysis")
if not os.path.exists(BVP_HOME):
    os.mkdir(BVP_HOME)

# default path for each persons dataset devided by state
# BVP_HOME/person/...

# DEBUG
# evaluate DS_Andreia dataset - clapagem 
# ds path
#test_path = "/home/msantos/Desktop/CINTESIS/DS_Andreia/csv/113027.csv"
#test_df = pd.read_csv(test_path, sep=";")


def evaluate_bvp(list_2_use, entropy_2_use, entropy_tolerance, entropy_dimension, compressor_2_use, compressor_level):
    """
    Computes entropy and compression of list_2_use.
    When entropy cannot be computed (2 data points or less) the 'error' is set to -2.0
    When compressed file is larger than the original, compression ratio will be displayed as negative
    Return a tuple containing the entropy, original and compressed sizes and the compression ratio
    :param list_2_use: data points to evaluate
    :param entropy_2_use: entropy to use
    :param entropy_tolerance: tolerance to consider when computing entropy
    :param entropy_dimension: matrix dimension to consider when computing entropy
    :param compressor_2_use: compressor to use
    :param compressor_level: level of compression of the compressor
    :return: (entropy result, original size, compressed size, compression ratio)
    """
    entropy_res, original_size, compression_res, comp_ratio = -2.0, 0.0, 0.0, 0.0
    # using -2.0 as an error value to avoid being miss-interpreted with relevant data
    pyeeg_entropy = "samp_entropy"
    if entropy_2_use == "apen":
        pyeeg_entropy = "ap_entropy"

    # NOTE: when then list of values does not have at least 3 values return -2 (lower than min of ap and samp entropy)
    # compute entropy (values, dimension, std_dev * tolerance) - use pyeeg
    list_sd = np.std(map(float,list_2_use))

    if len(list_2_use) > 2:
        tol_2_use = list_sd * entropy_tolerance

        entropy_method = getattr(sys.modules[pyeeg.__name__], pyeeg_entropy)
        entropy_res = entropy_method(list_2_use, entropy_dimension, tol_2_use)

    # compute compression
    compression_method = getattr(sys.modules[comp.__name__], compressor_2_use + '_compress')
    # since compressor use file as input, its easier to create and delete a temporary file
    temp_file = os.path.join(os.path.abspath("."), "temp_4_metrics.txt")
    util.write_list_to_file(file_2_write=temp_file, list_2_write=list_2_use)

    compression_data = compression_method(temp_file, compressor_level, False)  # False for decompress time
    original_size = compression_data.original
    compression_res = compression_data.compressed
    # compression ratio - compute only if original file is bigger that the compressed file
    if original_size >= compression_res:
        comp_ratio = util.compression_ratio(original_size, compression_res)
    else:  # original_size < compressed_size
        comp_ratio = float(100 - util.compression_ratio(original_size, compression_res))
    # delete temporary file used for compression and entropy
    os.remove(temp_file)
    return entropy_res, original_size, compression_res, comp_ratio


# receives the data frame (already devided by state) and compute the entropy
# and compression for each column desired
def compute_metrics_from_column(data_frame, state, entropy_2_use, entropy_tolerance, entropy_dimension,
                                compressor_2_use, compressor_level, with_compression_ratio=True, round_digits=4):
    """
    Receives data set and a state and computes the entropy, compression and compression ratio for each column of
    the data set. It is specifically applied to handle the columns: PIAS, PIAD and PIAM
    Returns a list (row entry for the final data set) with the entropy, compression( original and compressed sizes) and
    compression rate if flag is True
    :param data_frame: data frame to evaluate
    :param state: state being evaluated
    :param entropy_2_use: entropy method to use
    :param entropy_tolerance: tolerance to use when computing entropy
    :param entropy_dimension: matrix dimension to use when computing entropy
    :param compressor_2_use: compressor to use
    :param compressor_level: level of compression for the compressor
    :param with_compression_ratio: flag to add row with compression ratio
    :param round_digits: number of digits to use when rounding. 'None' avoid rounding
    :return:  list containing entropy, original and compressed sizes and compression ratio (depending on the flag)
    """
    # remove FC and Estado columns (1st and last columns)
    df_to_use = data_frame.ix[:,1:-1]
    final_list = [state]
    bvp_entropy, bvp_comp_original, bvp_comp_compressed, bvp_cr = list(), list(), list(), list()
    # compute metrics only from PIAS, PIAD and PIAM
    ncols = df_to_use.shape[1]
    for col in range(ncols):
        col_series = np.array(df_to_use.ix[:, col])
        col_ent, cp_original, cp_compressed, cr = evaluate_bvp(col_series, entropy_2_use=entropy_2_use,
                                                           entropy_tolerance= entropy_tolerance,
                                                           entropy_dimension = entropy_dimension,
                                                           compressor_2_use=compressor_2_use,
                                                           compressor_level=compressor_level)
        bvp_entropy.append(col_ent)
        bvp_comp_original.append(cp_original)
        bvp_comp_compressed.append(cp_compressed)
        bvp_cr.append(cr)

    # round entropy results only. compression values are integers
    final_list.extend(util.round_list(bvp_entropy, round_digits))
    final_compression_list = util.alternate_merge_lists(bvp_comp_original, bvp_comp_compressed)
    final_list.extend(final_compression_list)

    # round compression ratio with 2 decimals  - as it is percentage
    if with_compression_ratio:
        final_list.extend(util.round_list(bvp_cr, 2))

    return final_list


def divide_dataset_by_state(data_frame, specific_storage=None, sep2write=";", line_term="\n"):
    """
    Divide input data frame by state and return the results as a list of data frames
    If specific_storage is defined, stores the resulting data sets in the path provided
    :param data_frame: data frame to divide by state
    :param specific_storage: path to store the resulting state data frames
    :param sep2write: separator to use when writing the state data frames
    :param line_term: line terminator when writing the state data frames
    :return: list of the state data frames
    """
    df_list = list()
    states = pd.unique(data_frame.ix[: ,"Estado"])

    if specific_storage is not None:
        if not os.path.exists(specific_storage):
            os.mkdir(specific_storage)

    for state in states:
        df_by_state = data_frame[data_frame["Estado"].isin([state])]
        # if specific_storage is defined, the datasets are stored in the path given
        if specific_storage is not None:
            file_name = "%s_%s.csv" % (os.path.basename(specific_storage), state)
            storage_path = os.path.join(specific_storage, file_name)
            df_by_state.to_csv(storage_path, sep=sep2write, index=False,
                               line_terminator=line_term)

        df_list.append(df_by_state)

    return df_list


# ENTRY POINT FUNCTION
def clamp_analysis_from_file(input_path, entropy_2_use, entropy_tolerance, entropy_dimension,
                             compressor_2_use, compressor_level, with_compression_ratio=True,
                             sep2read=";", sep2write=";", line_term="\n",
                             store_by_state=True, output_path=None, compute_all=False):
    """
    # TODO: add documentation
    :param input_path:
    :param entropy_2_use:
    :param entropy_tolerance:
    :param entropy_dimension:
    :param compressor_2_use:
    :param compressor_level:
    :param with_compression_ratio:
    :param sep2read:
    :param sep2write:
    :param line_term:
    :param store_by_state:
    :param output_path:
    :param compute_all:
    :return:
    """
    # read csv to data frame
    data_frame = pd.read_csv(os.path.abspath(input_path), sep=sep2read, header="infer")

    # drop nan values
    data_frame = data_frame.dropna(axis=0, how='all')
    data_frame = data_frame.dropna(axis=1, how='all')

    # iterate over lines to discard lines with "perda" (only if dataset has more columns than expected)
    if data_frame.shape[1] > 6:
        data_frame = data_frame.drop(data_frame[data_frame.ix[:, -1].str.lower() == "perda"].index)
        # keep the first 6 columns - the rest only contain misleading data
        data_frame = data_frame.ix[:, 0:6]


    # remove the "minutos" column
    data_frame = data_frame.ix[:, 1:]

    # only keep PIAS, PIAD and PIAM for the output header - remove "estado"
    final_header = ["State"]
    header_2_map = list(data_frame.ix[:, 1:-1].keys())

    # Using the header (PIAS, PIAD, PIAM) create the final header:
    # State, Entropy_PIAS, Entropy_PIAD, Entropy_PIAM, Compression_PIAS_Original, Compression_PIAS_Compressed, ...,
    # PIAS_CRx100, ... - if flag is True
    # header for entropy
    header_ent = ["Entropy_" + s for s in header_2_map]
    final_header.extend(header_ent)
    # header for compression
    header_cp_original = ["%s_Size_Original" % s for s in header_2_map]
    header_cp_compressed = ["%s_Size_Compressed" % s for s in header_2_map]
    # merge cp headers with alternating indexes
    header_compression = util.alternate_merge_lists(header_cp_original, header_cp_compressed)
    final_header.extend(header_compression)
    if with_compression_ratio:
        # header for compression ratio
        header_cr = ["%s_CRx100" % s for s in header_2_map]
        final_header.extend(header_cr)

    specific_storage = None  # used if store_by_state flag is True
    if store_by_state:
        specific_storage = os.path.join(os.path.abspath("."), "csv_by_state", os.path.basename(input_path).split('.')[0])
        if not os.path.exists(specific_storage):
            os.makedirs(specific_storage)

    # divide data set by state
    df_list_by_state = divide_dataset_by_state(data_frame, sep2write=sep2write, line_term=line_term,
                                               specific_storage=specific_storage)

    # list of lists with metrics (entropy and compression) by state    
    metrics_list = list()
    # apply evaluate_bvp for PIAS, PIAD and PIAM for each dataset
    for index, df in enumerate(df_list_by_state):
        result_by_state = compute_metrics_from_column(data_frame=df, state=index, entropy_2_use=entropy_2_use,
                                                      entropy_tolerance=entropy_tolerance,
                                                      entropy_dimension=entropy_dimension,
                                                      compressor_2_use=compressor_2_use,
                                                      compressor_level=compressor_level,
                                                      with_compression_ratio = with_compression_ratio)

        metrics_list.append(result_by_state)

    # transform list of lists into data frame
    final_df = pd.DataFrame(metrics_list, columns=final_header)

    # store or return result
    file_name = "%s_%s_%s_%s_%s.csv" % (os.path.basename(input_path).split('.')[0], entropy_2_use, entropy_tolerance,
                                        compressor_2_use, compressor_level)

    if output_path is None:
        output_path = BVP_HOME

    output_path = util.remove_slash_from_path(output_path)

    # each individual file is kept in directory based on entropy and compressor parameters
    output_path = os.path.join(output_path, "%s_dim_%d_tol_%.2f_%s_lvl_%d" % (entropy_2_use, entropy_dimension,
                                                                              entropy_tolerance, compressor_2_use,
                                                                              compressor_level))

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    storage_path = os.path.join(output_path, file_name)

    print("Storing file into: " + os.path.abspath(storage_path))

    final_df.to_csv(storage_path,sep=sep2write,index=False, line_terminator=line_term)
    # only return the data frame if we want to gather every person in the same dataset
    if compute_all:
        return final_df

    return None


# TODO: add parser argument to only compute entropy or compression individually.
# TODO: enable entropy matrix dimension as argument to the functions - the parser already implements it

# ENTRY POINT FUNCTION
def clamp_analysis_from_dir(input_path, entropy_2_use, entropy_tolerance, entropy_dimension,
                            compressor_2_use, compressor_level, with_compression_ratio=True,
                            sep2read=";", sep2write=";", line_term="\n", store_by_state=True,
                            output_path=None, compute_all=False):
    """
    # TODO: add documentation
    :param input_path:
    :param entropy_2_use:
    :param entropy_tolerance:
    :param entropy_dimension:
    :param compressor_2_use:
    :param compressor_level:
    :param with_compression_ratio:
    :param sep2read:
    :param sep2write:
    :param line_term:
    :param store_by_state:
    :param output_path:
    :param compute_all:
    :return:
    """
    res_df_list = list()
    filenames_for_df = list()

    # for each dataset call clamp_analysis_from_file
    files_list = map(os.path.abspath,glob.glob("%s%s*" % (util.remove_slash_from_path(input_path), os.sep)))

    for csv_file in files_list:
        res_df = clamp_analysis_from_file(input_path=csv_file, entropy_2_use=entropy_2_use,
                                          entropy_tolerance=entropy_tolerance, entropy_dimension=entropy_dimension,
                                          compressor_2_use=compressor_2_use, compressor_level=compressor_level,
                                          sep2read=sep2read, sep2write=sep2write, line_term=line_term,
                                          store_by_state=store_by_state, output_path=output_path,
                                          with_compression_ratio=with_compression_ratio, compute_all=compute_all)

        if compute_all:
            num_of_states = pd.unique(res_df.ix[:, 0]).size  # compute the number of different states
            # repeat the filename to append to the csv with every person (enable repetition)
            filenames_for_df.extend([util.remove_file_extension(os.path.basename(csv_file))] * num_of_states)
            res_df_list.append(res_df)

    if compute_all:
        column_filename = pd.DataFrame(filenames_for_df, columns=["Filename"])

        # concatenate every dataset
        all_dfs = pd.concat(res_df_list, axis=0, ignore_index=True)

        # finally add the filename column
        result_df = pd.concat([column_filename, all_dfs], axis=1)

        # store the result data set
        final_ds_name = os.path.join(BVP_HOME, ("clampage_analysis_global_%s_dim_%d_tol_%.1f_%s_lvl_%d.csv" %
                                                (entropy_2_use, entropy_dimension, entropy_tolerance,
                                                 compressor_2_use, compressor_level)))

        # write csv
        print("Storing file into: " + os.path.abspath(final_ds_name))
        result_df.to_csv(final_ds_name, sep=sep2write, index=False, line_terminator=line_term)


def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse parser or subparser,
    and are the optional arguments for the invoked modules
    """
    parser.add_argument("-dss",
                        "--dont-store-state",
                        dest="store_by_state",
                        action="store_false",
                        default=True,
                        help="Avoid storing each data set generated while dividing by the clampage state;"
                             " [default:%(default)s]")

    parser.add_argument("-ncr",
                        "--no-compression-ratio",
                        dest="compression_ratio",
                        action="store_false",
                        default=True,
                        help="Avoid adding an additional column to the resulting dataset with the compression ratio;"
                             " [default:%(default)s]")

    parser.add_argument("-aio",
                        "--all-in-one",
                        dest="compute_all",
                        action="store_true",
                        default=False,
                        help="Store every data set evaluated into a single dataset; [default:%(default)s]")
