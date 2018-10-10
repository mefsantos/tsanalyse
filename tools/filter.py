"""
Copyright (C) 2012 Mara Matias
Edited by Marcelo Santos - 2016


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


Disclaimer: This module is very specific to our data sets. The dataset files are
always either two columns -- the first is the time and the second the heat rate frequency
or rr interval -- or more columns where the first column is timestamps and the second
the hrf which in these files has to be divided by 1000 to get the usual three digit
number.

Depending on the passed options the module either extracts the timestamp and
heart rate frequency(hrf) or just the hrf. 

Optionally a limit may be applied to eliminate signal loss, we consider the
signal to be lost if hrf is below 50 or above 250. If a particular line is
considered as signal lost it is omitted from the resulting file.

ENTRY POINT: clean(input_name,dest_dir, keep_time=False, apply_limits=False)
"""

import os
import logging
import utilityFunctions as util

module_logger = logging.getLogger('tsanalyse.filter')


# TODO: change printouts to logger
# ENTRY POINT FUNCTIONS
def ds_filter(input_name, dest_dir, keep_time=False, apply_limits=False, round_to_int=False, hrf_col=1):
    """
    (str,str,bool,bool,bool) -> Nonetype

    Cleans the file or every file from a directory named input_name,
    and saves the resulting files in dest_dir, optionally the
    time stamp is kept and the limits(50-250) are applied.

    :param input_name: name of the dataset to read
    :param dest_dir: output directory
    :param keep_time: flag to keep the time column of the original dataset
    :param apply_limits: flag to apply limits between sections
    :param round_to_int: flag to round the time series to integer

    """
    module_logger.debug("The input name received: %s" % input_name)
    if os.path.isdir(input_name):
        filelist = util.listdir_no_hidden(input_name)
        for filename in filelist:
            clean_file(os.path.join(input_name, filename.strip()),
                       os.path.join(dest_dir, filename.strip()),
                       keep_time, apply_limits, round_to_int=round_to_int, hrf_col=hrf_col)
    else:
        filename = os.path.basename(input_name)
        clean_file(input_name,
                   os.path.join(dest_dir, filename.strip()),
                   keep_time, apply_limits, round_to_int=round_to_int, hrf_col=hrf_col)


# IMPLEMENTATION
def clean_file(input_file, dest_file, keep_time, apply_limits, round_to_int=False, hrf_col=1):
    """

    (str, str, bool, bool) -> NoneType

    Clean operation of a single file.

    :param input_file: file to read
    :param dest_file: output file
    :param keep_time: flag to keep the time column of the original dataset
    :param apply_limits: flag to apply limits between sections
    :param round_to_int: flag to round the time series to integer

    """
    floating_point_param = "%.3f\n"
    if round_to_int:
        floating_point_param = "%d\n"
    with open(input_file, "rU") as fdin:
        with open(dest_file, "w") as fdout:
            for line in fdin:
                data = line.split()

                # to filter any headers the file might have, this operates under the assumption
                # that headers never start with a number.
                try:
                    float(data[0])
                except ValueError:
                    continue
                if len(data) != 0:
                    module_logger.info("filtering file: %s" % input_file)
                    try:
                        float(data[hrf_col])
                    except IndexError:
                        module_logger.warning("Index out of range. Falling back to column 1")
                        hrf_col = 1
                        continue
                    except ValueError:
                        module_logger.warning("Value Error. Falling back to column 1")
                        hrf_col = 1
                        continue
                    hrf = float(data[hrf_col])
                    if hrf >= 1000:
                        hrf = round(float(data[hrf_col]) / 1000, 3)
                    if round_to_int:
                        hrf = round(hrf)
                    if not apply_limits:
                        if keep_time:
                            time = data[0]
                            fdout.write("%s " % time)
                        fdout.write(floating_point_param % hrf)
                    elif 50 <= hrf <= 250:
                        if keep_time:
                            time = data[0]
                            fdout.write("%s " % time)
                        fdout.write(floating_point_param % hrf)
    module_logger.info("Storing file in: %s" % os.path.abspath(dest_file))


# AUXILIARY FUNCTIONS

def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    """

    parser.add_argument("-col",
                        "--hrf-column",
                        dest="hrf-col",
                        metavar="HRF-COLUMN",
                        action="store",
                        default=1,
                        type=int,
                        help="column in the dataset to extract hrf from; [default: %(default)s]")
    parser.add_argument("-kt",
                        "--keep-time",
                        dest="keep_time",
                        action="store_true",
                        default=False,
                        help="When filtering keep both the hrf and time stamp")

    parser.add_argument("-lim",
                        "--apply-limits",
                        dest="apply_limits",
                        action="store_true",
                        default=False,
                        help="When filtering apply limit cutoffs, i.e., 50 <= hrf <= 250")

    parser.add_argument("-rint",
                        "--round-to-int",
                        dest="round_to_int",
                        action="store_true",
                        # default=False,
                        help="Round hrf values to integer")

