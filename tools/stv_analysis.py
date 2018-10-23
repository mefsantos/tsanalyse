"""
Copyright (C) 2017 Marcelo Santos

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

...

MODULE EXTERNAL DEPENDENCIES:
pandas(http://pandas.pydata.org/),
numpy(http://numpy.scipy.org/)


ENTRY POINT:
    compute_stv_metrics(input_path, options)

_______________________________________________________________________________

IMPLEMENTATION NOTES:
- first we compute the T(i), aka interbeat interval, from the F(i), aka HRF, for the algorithms,
 using the formula:
    T(i) = 60000 / F(i)

- Then we parametrize the formula used on several algorithms given as:

  sum_max_lim
 SUM |(Param_1 - Param_2)| / divisor
  sum_start
"""


import os
import sys
import glob
import pandas
import logging
import numpy as np
import tools.utilityFunctions as util

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util


module_logger = logging.getLogger('tsanalyse.stv')

CONSIDER_NANS = False

AVAILABLE_ALGORITHMS = ["arduini", "arduini_mod", "dalton", "organ", "sonicaid", "yeh", "zugaiv",
                        "sd", "sd_subsets"]
# number of RR Intervals = number_of_interbeat_intervals + 1, i.e. len(Ti)


def interbeat_interval_from_list(list_to_eval):
    """
    Compute the inter-beat interval based on the heart rate frequency (hrf) in bpm from a list
    :param list_to_eval: list of heart rate frequencies
    :return: list of inter-beat intervals in milliseconds
    """
    return map((lambda hrf: float(60000)/hrf), list_to_eval)


# ARDUINI's algorithms
def list_preparation_to_extract_ti(time_series_to_eval, duration_of_subset_in_seconds=60.0, sampling_frequency=4):
    """
    Partition the time_series in subset of 60 seconds. Since we use 4Hz, its 240 samples per subset.
    If the last subset does not contain enough samples, discard it
    :param time_series_to_eval:
    :param duration_of_subset_in_seconds:
    :param sampling_frequency:
    :return:
    """
    # Constants defined by the algorithm
    samples_per_subset = (duration_of_subset_in_seconds * sampling_frequency)

    # Preparation
    list_of_lists = util.list_of_lists_with_size(time_series_to_eval, int(samples_per_subset))

    # only consider the lists with 'samples_per_subset' elements
    list_of_subsets = filter((lambda lst: len(lst) == samples_per_subset), list_of_lists)
    interbeat_intervals_of_subsets = map(interbeat_interval_from_list, list_of_subsets)
    module_logger.debug("Interbeat interval of lists: %s" % interbeat_intervals_of_subsets)

    return interbeat_intervals_of_subsets


def loop_result_for_parametrized_sum(iter_start, iter_end, list_to_eval, divisor):
    list_of_res = []
    for i in range(iter_start, iter_end):
        list_of_res.append(float(abs(list_to_eval[i+1] - list_to_eval[i])) / divisor)
    return sum(list_of_res)


def loop_result_for_parametrized_sum_order_inverted(iter_start, iter_end, list_to_eval, divisor):
    list_of_res = []
    for i in range(iter_start, iter_end):
        list_of_res.append(float(abs(list_to_eval[i] - list_to_eval[i-1])) / divisor)
    return sum(list_of_res)


# NOTE: these two NP_* functions may cause ZeroDivisionError since X/nan = nan but X / 0 = Error.
# We will protect the division with the 'will_be_divider' flag
def np_mean_to_use(input_data, will_be_divider=False):
    if not CONSIDER_NANS and not will_be_divider:
        return np.nanmean(input_data) if not util.is_nan_list(input_data) else 0.0
    return np.mean(input_data)


def np_median_to_use(input_data, will_be_divider=False):
    if not CONSIDER_NANS and not will_be_divider:
        return np.nanmedian(input_data) if not util.is_nan_list(input_data) else 0.0
    return np.median(input_data)


def np_std_to_use(input_data):
    return np.std(input_data) if CONSIDER_NANS else np.nanstd(input_data)


def stv_arduini(time_series_to_eval, sampling_frequency=4):
    """
    :param time_series_to_eval:
    :param sampling_frequency: the sampling frequency in hertz
    :return:
    """
    # Preparation
    list_of_subsets = list_preparation_to_extract_ti(time_series_to_eval, 60, sampling_frequency)

    # The actual algorithm - apply the algorithm to every subset
    resulting_list = map((lambda lst: loop_result_for_parametrized_sum(0, len(lst)-1, lst, len(lst)-1)), list_of_subsets)
    return resulting_list


def stv_arduini_mod(time_series_to_eval, sampling_frequency=4):
    """
    Arduini Mod - uses HRF_mean instead the number of samples
    :param time_series_to_eval:
    :param sampling_frequency:
    :return:
    """
    # Preparation
    list_of_subsets = list_preparation_to_extract_ti(time_series_to_eval, 60, sampling_frequency)
    # Algorithm run
    resulting_list = map((lambda lst: loop_result_for_parametrized_sum(0, len(lst)-1, lst, np_mean_to_use(lst, True))), list_of_subsets)
    return resulting_list


# DALTON
def stv_dalton(time_series_to_eval, sampling_frequency=4):
    # Preparation
    list_of_subsets = list_preparation_to_extract_ti(time_series_to_eval, 60, sampling_frequency)
    # Algorithm run
    resulting_list = map((lambda lst: loop_result_for_parametrized_sum_order_inverted(1, len(lst), lst, 2)), list_of_subsets)
    return resulting_list


# Organ
def stv_organ(time_series_to_eval, sampling_frequency=4):
    # Uses FHR directly
    # Preparation
    samples_per_subset = (30 * sampling_frequency)
    list_of_lists = util.list_of_lists_with_size(time_series_to_eval, samples_per_subset)
    # only consider the lists with 'samples_per_subset' elements
    list_of_subsets = filter((lambda lst: len(lst) == samples_per_subset), list_of_lists)
    # Algorithm run
    resulting_list = map((lambda lst: loop_result_for_parametrized_sum(0, len(lst)-1, lst, np_mean_to_use(lst, True))), list_of_subsets)
    return resulting_list


# Sonicaid
def stv_sonicaid(time_series_to_eval, sampling_frequency=4):
    # Algorithm constants
    subset_duration_in_seconds = 3.75
    # divide time series into subsets of 3.75 (15 samples for 4Hz)
    subsets_of_3_75 = list_preparation_to_extract_ti(time_series_to_eval,
                                                     sampling_frequency=sampling_frequency,
                                                     duration_of_subset_in_seconds= subset_duration_in_seconds)

    # compute the normal sum for each subset
    subsets_of_rm = map((lambda lst: loop_result_for_parametrized_sum(0, len(lst)-1, lst, np_mean_to_use(lst))), subsets_of_3_75)

    # then apply the general formula 1/h(1_sum_h(|R_m+1 - R_m|))
    h = len(subsets_of_rm)-1
    res = []
    for i in range(0, h):
        res.append(abs(subsets_of_rm[i+1] - subsets_of_rm[i]))
    return 1/float(h) * sum(res)


# Van Geijn
def compute_ti_prime_at_index(ti_series, index):
    return (ti_series[index-1] + ti_series[index])/2


def compute_gi_at_index(list_2_eval, index):
    return pow(180 / float(compute_ti_prime_at_index(list_2_eval, index) - 320), 1.5)


def van_geijn_formula(ti_list):
    res_list = []
    # compute gi = (180 / (Ti' - 320))^1.5
    # compute Ti' = (Ti-1 + Ti) / 2
    for i in range(1, len(ti_list)-1):
        res_list.append(compute_gi_at_index(ti_list, i) * (ti_list[i] - ti_list[i-1]))
    return util.compute_iqr(res_list)


def stv_van_geijn(time_series_to_eval, sampling_frequency=4):
    duration_of_subsets_in_seconds = 30
    # generate Ti subsets of 30 seconds
    lol_of_ti_subsets_of_30s = list_preparation_to_extract_ti(time_series_to_eval=time_series_to_eval,
                                                              duration_of_subset_in_seconds=duration_of_subsets_in_seconds,
                                                              sampling_frequency=sampling_frequency)

    # compute formula: IQR[gi* (Ti - Ti-1)]
    van_geijn_list = map(lambda lst: van_geijn_formula(lst), lol_of_ti_subsets_of_30s)
    return van_geijn_list


# Yeh
def compute_di_at_index(ti_list, index):
    return 1000 * ((ti_list[index] - ti_list[index+1]) / (ti_list[index] + ti_list[index+1]))


def compute_dave(ti_list):
    di_res = []
    for i in range(0, len(ti_list)-1):
        di_res.append(compute_di_at_index(ti_list, i))
    return sum(di_res)/np_mean_to_use(ti_list)


def yeh_formula(list_2_eval):
    res_list = []
    for i in range(0,len(list_2_eval)-1):
        res_list.append(pow(
            (compute_di_at_index(list_2_eval, i) - compute_dave(list_2_eval)), 2) / float(np_mean_to_use(list_2_eval)))
    return pow(sum(res_list), 0.5)


def stv_yeh(time_series_to_eval, sampling_frequency=4):
    # get Tis of 60 sec
    duration_of_subset_in_seconds = 60
    ti_subsets_of_60s = list_preparation_to_extract_ti(time_series_to_eval=time_series_to_eval,
                                                       duration_of_subset_in_seconds=duration_of_subset_in_seconds,
                                                       sampling_frequency=sampling_frequency)
    return map(lambda lst: yeh_formula(lst), ti_subsets_of_60s)


# Zugaiv
def zugaiv_formula(list_to_eval):
    vi_list = []
    for i in range(0, len(list_to_eval)-1):
        vi_list.append((list_to_eval[i+1] - list_to_eval[i])/float(list_to_eval[i+1] + list_to_eval[i]))
    # sum_part = sum(map((lambda vi: vi_md(vi,np.median(vi_list))), vi_list))

    return (1 / float(len(list_to_eval)-1)) * sum(map((lambda vi: abs(vi - np_median_to_use(vi_list))), vi_list))


def stv_zugaiv(time_series_to_eval, sampling_frequency=4):
    """
    Generate Ti From FHR. Then partition the Ti list into subsets with the number of samples equivalent to
    128 beats (127 samples). After that simply apply the algorithm
    :param time_series_to_eval:
    :param sampling_frequency:
    :return:
    """
    # generate Ti.
    list_of_ti = interbeat_interval_from_list(time_series_to_eval)
    # create subsets of 127 samples
    subsets_of_128_beats = util.list_of_lists_with_size(list_of_ti, 127)
    # filter the subsets to contain exactly 127 samples = 128 beats. discard the last set of condition is not met
    list_of_subsets = filter((lambda lst: len(lst) == 127), subsets_of_128_beats)
    # general formula
    result_sets = map(lambda lst: zugaiv_formula(lst), list_of_subsets)
    return result_sets


def stv_sd_subsets(time_series_to_eval,  sampling_frequency=4, duration_in_seconds=60):
    subsets_size = sampling_frequency * duration_in_seconds
    lol_of_subsets = util.list_of_lists_with_size(time_series_to_eval, subsets_size)
    return map(lambda subset: np_std_to_use(subset), lol_of_subsets)


# need this dummy param so that i can use method_to_call()
def stv_sd(time_series_to_eval, sampling_frequency=4):
    return np_std_to_use(time_series_to_eval)


# TODO: add parameter for duration of the subsets if needed and standardize every function to the same parameters
def compute_stv_metric_of_file(input_file_name, algorithm_name, sampling_frequency=4,
                               round_digits=None, consider_nans=False):

    dataframe = pandas.read_csv(input_file_name)
    result_entry_with_filename_and_metrics = [os.path.basename(input_file_name)]

    list_to_eval = list(dataframe.ix[:, 0])
    method_to_call = globals()["stv_%s" % algorithm_name]
    result = util.my_round(method_to_call(list_to_eval, sampling_frequency), round_digits)
    result_entry_with_filename_and_metrics.append(util.my_round(np_mean_to_use(result), round_digits))
    result_entry_with_filename_and_metrics.append(util.my_round(np_median_to_use(result), round_digits))
    result_entry_with_filename_and_metrics.append(util.my_round(np_std_to_use(result), round_digits))

    if type(result) == list:
        result_entry_with_filename_and_metrics.extend(result)
    else:
        result_entry_with_filename_and_metrics.append(result)
    return result_entry_with_filename_and_metrics


# TODO: add entry point for a single file and not only a directory - use 'compute_stv_metrics'
def compute_stv_metric_of_directory(input_path, algorithm_name, sampling_frequency=4, round_digits=None,
                                    consider_nans=False, output_path=None):

    if output_path is None:
        output_path = util.STV_ANALYSIS_STORAGE_PATH
        module_logger.debug("Output path was not defined. Using default: %s" % output_path)

    if not os.path.exists(output_path):
        module_logger.debug("Creating %s..." % output_path)
        os.mkdir(output_path)

    if algorithm_name.lower() == "all":
        map(lambda algo: compute_stv_metric_of_directory(input_path, algo, sampling_frequency,
                                                         round_digits, consider_nans), AVAILABLE_ALGORITHMS)
    else:
        if algorithm_name in AVAILABLE_ALGORITHMS:
            module_logger.debug("Running algorithm %s" % algorithm_name)
            files_list = map(os.path.abspath, glob.glob("%s%s*" % (util.remove_slash_from_path(input_path), os.sep)))
            result_list = map(lambda filename: compute_stv_metric_of_file(filename, algorithm_name, sampling_frequency,
                                                                          round_digits, consider_nans),
                              files_list)
            # generate the header based on the longest list
            header_from_list = util.generate_header_from_list_with_string(max(result_list, key=len), "Subset")
            # first is for the name
            metrics_header = ["Filename", "Mean", "Median", "Std_Dev"]

            metrics_header.extend(header_from_list[:-3])
            # last three are mean, median and stdev

            res_dataframe = pandas.DataFrame(result_list, columns=metrics_header)

            final_path = os.path.join(output_path, ("stv_analysis_using_%s.csv" % algorithm_name))
            res_dataframe.to_csv(final_path, sep=";", index=False)
            module_logger.info("Storing file into: " + os.path.abspath(final_path))
        else:
            error_message = "Algorithm chosen is not available. Make sure you typed correctly using one of the " \
                            "following options: all, " + ", " .join(AVAILABLE_ALGORITHMS)
            module_logger.error(error_message)
            raise IOError(error_message)


# need extra code to finish - decide how to output these small analysis
# for now it will be the entry point only to validate the input
# ENTRY POINT
def compute_stv_metrics(input_path, options):

    global CONSIDER_NANS  # this is required so we can set the global variable instead of a local one w'the same name
    CONSIDER_NANS = options["use_nan"]

    if os.path.isfile(input_path):
        message = "This module only accepts directories as input. " \
                  "Consider changing you INPUT_PATH\n\tfrom: %s\n\tto:%s" % (os.path.abspath(input_path),
                                                                         os.path.dirname(os.path.abspath(input_path)))
        module_logger.warning(message)
        # file_name = os.path.basename(input_path)
        # output_dir_path = util.RUN_ISOLATED_FILES_PATH
        # result_ds = compute_stv_metric_of_file(input_path, options['algorithm'], options['sampling_frequency'])
        # if output_path:
        #     if os.path.exists(output_path): # otherwise we use the default
        #         output_dir_path = output_path
        # output_name = "%s_%s_%s.csv" % (output_dir_path, file_name.replace(".", "_"), options["algorithm"])
        # output_file_path = os.path.join(output_dir_path, output_name)
        # # result_ds.to_csv(output_file_path , sep=";", index=False)
        # print(result_ds)
    else:
        compute_stv_metric_of_directory(input_path, options['algorithm'], options['sampling_frequency'],
                                        options["round_digits"], options["use_nan"],
                                        output_path=options["output_path"])


# TODO: validate parser input
def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse parser or subparser,
    and are the optional arguments for the invoked modules
    """
    parser.add_argument("-algo",
                        "--algorithm",
                        dest="algorithm",
                        action="store",
                        default="all",
                        help="Specifies the algorithm to use for the analysis. "
                             "Available algorithms: " + ", " .join(AVAILABLE_ALGORITHMS) +
                             ". If option is 'all' Every algorithm will be used; [default:%(default)s].")
                             # "\nNOTE: Van Geijn algorithm only works for signals with heart rate frequency lower"
                             # " than 192 bpm, otherwise the IQR cannot be computed due to formula's specifications.")

    parser.add_argument("-sf",
                        "--sampling-frequency",
                        dest="sampling_frequency",
                        action="store",
                        default=4,
                        help="Specifies the sampling frequency of the samples to data analyse; [default:%(default)s]")

    parser.add_argument("-wnan", "--with-nan", dest="use_nan", action="store_true", default=False,
                        help="Specify whether or not to ignore NAN (Not a Number) entries in mean/median calculations;"
                             " [default:%(default)s].\nNOTE: mean/median of lists with nans will also be nan.")
