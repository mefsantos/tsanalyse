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

ENTRY POINT: clean(input_name,dest_dir, keep_time=False, cutoff_limits=[50,250])
"""

import os
import shutil
import logging
import utilityFunctions as util
import constants

module_logger = logging.getLogger('tsanalyse.filter')

CUTOFF_LIMITS = constants.DEFAULT_CUTOFF_LIMITS


# ENTRY POINT FUNCTIONS
def ds_filter(input_name, dest_dir, keep_time=False, cutoff_limits=CUTOFF_LIMITS,
              round_to_int=False, hrf_col=1, suffix=None):
    """
    (str,str,bool,bool,bool) -> Nonetype

    Cleans the file or every file from a directory named input_name,
    and saves the resulting files in dest_dir, optionally the
    time stamp is kept and the limits(50-250) are applied.

    :param input_name: name of the dataset to read
    :param dest_dir: output directory
    :param keep_time: flag to keep the time column of the original dataset
    :param cutoff_limits: the cutoff limits to apply to the hrf
    :param round_to_int: flag to round the time series to integer
    :param hrf_col: column to parse the hrf values
    :param suffix: suffix to add to the destination file name. Used when user specifies the output location but
                    runs individual files.

    """
    module_logger.debug("The input name received: %s" % input_name)
    module_logger.debug("Suffix: %s" % suffix)
    if os.path.isdir(input_name):
        filelist = util.listdir_no_hidden(input_name)
        for filename in filelist:
            clean_file(os.path.join(input_name, filename.strip()),
                       os.path.join(dest_dir, filename.strip()),
                       keep_time, cutoff_limits, round_to_int=round_to_int, hrf_col=hrf_col)
    else:
        filename = os.path.basename(input_name)
        dest_file = filename
        module_logger.debug("dest filename: %s" % dest_file)
        if suffix:
            # we de-construct and re-construct the filename with the suffix (filtered / filtered_wtime)
            dest_file_list = filename.split(".")
            dest_file_list.insert(1, suffix)
            module_logger.debug("destination file list: %s" % dest_file_list)
            dest_file = "%s.%s" % ("".join(dest_file_list[:-1]), dest_file_list[-1])
            module_logger.debug("destination file after split and insert: %s" % dest_file)
            print(dest_file)
        dest_filename = os.path.join(dest_dir, dest_file)
        clean_file(input_name, dest_filename,
                   keep_time, cutoff_limits, round_to_int=round_to_int, hrf_col=hrf_col)


# IMPLEMENTATION
def clean_file(input_file, dest_file, keep_time, cutoff_limits, round_to_int=False, hrf_col=1):
    """

    (str, str, bool, bool) -> NoneType

    Clean operation of a single file.

    :param input_file: file to read
    :param dest_file: output file
    :param keep_time: flag to keep the time column of the original dataset
    :param cutoff_limits: the cutoff limits to apply to the hrf
    :param round_to_int: flag to round the time series to integer
    :param hrf_col: column to parse the hrf values

    """
    single_column_dataset = False
    floating_point_param = "%.3f\n"
    if round_to_int:
        floating_point_param = "%d\n"

    # we will only process if the file is not empty
    try:
        file_size = os.path.getsize(input_file)
    except OSError as error:
        module_logger.critical("%s. Skipping..." % error[1])
    else:
        if file_size <= 0:
            module_logger.warning("File '%s' is empty. Skipping ..." % util.remove_project_path_from_file(input_file))
            return
        line_number = 0
        with open(input_file, "rU") as fdin:
            with open(dest_file, "w") as fdout:
                module_logger.info("processing file: %s" % input_file)
                for line in fdin:
                    data = line.split()
                    line_number += 1

                    # to filter any headers the file might have, this operates under the assumption
                    # that headers never start with a number.
                    # the first time we get a Value Error we ignore the line (assume to be a header)
                    try:
                        float(data[0])
                    except ValueError as ve:
                        module_logger.warning("String found. Assuming its the header. Skipping line...")
                        continue
                    try:
                        float(data[1])
                    except IndexError:
                        module_logger.warning("Index out of range. The dataset should contain at least two columns."
                                              " Skipping ...")
                        single_column_dataset = True
                        break
                    except ValueError as ve:
                        module_logger.critical("Value Error (%s. line: %d, column: %d). Corrupted file."
                                               " Skipping..." % (ve, line_number, 2))
                        single_column_dataset = True
                        break
                    else:
                        if len(data) != 0:
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
                            if not cutoff_limits:
                                if keep_time:
                                    time = data[0]
                                    fdout.write("%s " % time)
                                fdout.write(floating_point_param % hrf)

                            elif min(cutoff_limits) <= hrf <= max(cutoff_limits):
                                if keep_time:
                                    time = data[0]
                                    fdout.write("%s " % time)
                                fdout.write(floating_point_param % hrf)

        if not single_column_dataset:
            module_logger.info("Storing file in: %s" % os.path.abspath(dest_file))
        else:
            module_logger.info("Deleting corrupt output file...")
            try:
                os.remove(dest_file)
            except OSError as error:
                module_logger.warning("%s. Skipping..." % error[1])

        # if os.path.getsize(dest_file) <= 0:
        #     module_logger.warning("File '%s' is empty" % os.path.basename(dest_file))


# AUXILIARY FUNCTIONS
def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    """

    parser.add_argument("-col",
                        "--column",
                        dest="column",
                        metavar="COLUMN",
                        action="store",
                        default=1,
                        type=int,
                        help="Column in the dataset to extract hrf from; [default: %(default)s]")
    parser.add_argument("-kt",
                        "--keep-time",
                        dest="keep_time",
                        action="store_true",
                        default=False,
                        help="When filtering keep both the hrf and time stamp")
    parser.add_argument('-lims',
                        '--cutoff-limits',
                        dest="limits",
                        nargs=2,
                        type=int,
                        metavar=('LOWER', 'UPPER'),
                        default=None,
                        help='When filtering apply limit cutoffs, i.e., LOWER <= hrf <= UPPER.')
    parser.add_argument("-rint",
                        "--round-to-int",
                        dest="round_to_int",
                        action="store_true",
                        # default=False,
                        help="Round hrf values to integer")

