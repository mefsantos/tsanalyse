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

...

MODULE EXTERNAL DEPENDENCIES:
pandas(http://pandas.pydata.org/)

ENTRY POINT:

    ...


- first we need to compute the T(i), aka interbeat interval, from the F(i), aka HRF, for the algorithms,
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
import numpy as np

try:
    import utilityFunctions as util
except ImportError:
    import tools.utilityFunctions as util


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
    # print("\n list of lists:\n %s" % list_of_lists)

    # only consider the lists with 'samples_per_subset' elements
    list_of_subsets = filter((lambda lst: len(lst) == samples_per_subset), list_of_lists)
    interbeat_intervals_of_subsets = map(interbeat_interval_from_list, list_of_subsets)
    # print("\n interbeat interval of lists:\n%s" % interbeat_intervals_of_subsets)

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
    resulting_list = map((lambda lst: loop_result_for_parametrized_sum(0, len(lst)-1, lst, np.mean(lst))), list_of_subsets)
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
    resulting_list = map((lambda lst: loop_result_for_parametrized_sum(0, len(lst)-1, lst, np.mean(lst))), list_of_subsets)
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
    subsets_of_rm = map((lambda lst: loop_result_for_parametrized_sum(0, len(lst)-1, lst, np.mean(lst))), subsets_of_3_75)

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
    return sum(di_res)/np.mean(ti_list)


def yeh_formula(list_2_eval):
    res_list = []
    for i in range(0,len(list_2_eval)-1):
        res_list.append(pow(
            (compute_di_at_index(list_2_eval, i) - compute_dave(list_2_eval)), 2) / float(np.mean(list_2_eval)))
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

    return (1 / float(len(list_to_eval)-1)) * sum(map((lambda vi: abs(vi - np.median(vi_list))), vi_list))


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
    return map(lambda subset: np.std(subset), lol_of_subsets)


def stv_sd(time_series_to_eval):
    return np.std(time_series_to_eval)

# # test example - arduini standard
# csv_path = "/home/msantos/Desktop/CINTESIS/Rotinas/hrfanalyse-master/unittest_dataset_clean/S0001312.txt"
# dataframe = pandas.read_csv(csv_path)
# simple_list = list(dataframe.ix[:, 0])
# # l1 = stv_arduini(simple_list)
# # l2 = stv_arduini_mod(simple_list)
# # l3 = stv_dalton(simple_list)
# # l4 = stv_organ(simple_list)
# # l5 = stv_sonicaid(simple_list)
# # l6 = stv_zugaiv(simple_list)
# l7 = stv_van_geijn(simple_list)


# TODO: add parameter for duration of the subsets if needed and standardize every function to the same parameters
def compute_stv_metric_of_file(input_file_name, algorithm_name, sampling_frequency=4):
    dataframe = pandas.read_csv(input_file_name)
    result_entry_with_filename_and_metrics = [os.path.basename(input_file_name)]

    list_to_eval = list(dataframe.ix[:, 0])
    method_to_call = globals()["stv_%s" % algorithm_name]
    result = method_to_call(list_to_eval, sampling_frequency)
    result_entry_with_filename_and_metrics.append(np.mean(result))
    result_entry_with_filename_and_metrics.append(np.median(result))
    result_entry_with_filename_and_metrics.append(np.std(result))
    if type(result) == list:
        result_entry_with_filename_and_metrics.extend(result)
    else:
        result_entry_with_filename_and_metrics.append(result)
    return result_entry_with_filename_and_metrics


# ENTRY POINT
def compute_stv_metric_of_directory(input_path, algorithm_name, sampling_frequency=4,
                                    output_path=None, drop_na=False):

    if output_path is None:
        base_path = os.path.dirname(os.path.abspath(util.remove_slash_from_path(input_path)))
        output_path = os.path.join(base_path, "stv_algorithms")

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    if algorithm_name.lower() == "all":
        map(lambda algo: compute_stv_metric_of_directory(input_path, algo, sampling_frequency), AVAILABLE_ALGORITHMS)
    else:
        if algorithm_name in AVAILABLE_ALGORITHMS:
            files_list = map(os.path.abspath, glob.glob("%s%s*" % (util.remove_slash_from_path(input_path), os.sep)))
            result_list = map(lambda filename: compute_stv_metric_of_file(filename, algorithm_name, sampling_frequency),
                              files_list)
            # generate the header based on the longest list
            header_from_list = util.generate_header_from_list_with_string(max(result_list, key=len), "Subset")
            # first is for the name
            metrics_header = ["Filename", "Mean", "Median", "Std_Dev"]

            metrics_header.extend(header_from_list[:-3])
            # last three are mean, median and stdev

            res_dataframe = pandas.DataFrame(result_list, columns=metrics_header)

            # if(drop_na):
            # res_dataframe.replace(r'\s', np.nan, regex=True)
            # res_dataframe.dropna(axis='columns',how='any')

            final_path = os.path.join(output_path, ("stv_analysis_using_%s.csv" % algorithm_name))
            res_dataframe.to_csv(final_path, sep=";", index=False)
            print("Storing file into: " + os.path.abspath(final_path))
        else:
            raise IOError("Algorithm chosen is not available. Make sure you typed correctly using one of the "
                          "following options: all, " + ", " .join(AVAILABLE_ALGORITHMS))


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
                             ". If option is 'all' Every algorithm will be used; [default:%(default)s]. "
                             "\nNOTE: Van Geijn algorithm only works for signals with heart rate frequency lower"
                             " than 192 bpm, otherwise the IQR cannot be computed due to formula's specifications.")

    parser.add_argument("-sf",
                        "--sampling-frequency",
                        dest="sampling_frequency",
                        action="store",
                        default=4,
                        help="Specifies the sampling frequency of the samples to data analyse; [default:%(default)s]")
