#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (C) 2018 Marcelo Santos

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


TSFilter is a command line interface that allows you to apply filter
      operations. Filtering a file means extracting the heart rate
      frequencies (timestamps may also be saved).

      OUTCOME: This interface's execution will create a new directory with a
      '_filtered' appended to the original directory's name were all the
      filtered files are saved (this directory is created whether you
      call this interface on a directory or file).

      COMMAND_OPTIONS for this command are:

       -lim, --apply-limits     When filtering apply limit cutoffs (50<=hrf<=250)

       -kt, --keep-time         When cleaning keep both the hrf and the timestamp

       -rint, --round-to-int    Round the hrf values to int

       -col HRF-COLUMN, --hrf-column HRF-COLUMN
                                Column in the dataset to extract hrf from; [default:1]

Examples:

     Retrieve the hrf within the limits [50, 250]:
     ./TSFilter.py unittest_dataset filter -lim

      Retrieve the timestamps and hrf
     ./TSFilter.py unittest_dataset filter -kt

       Retrieve the hrf from the second column of the input file
     ./TSFilter.py unittest_dataset filter -col 2


"""

# TODO: add a parser flag "force-output" that will create the output directory if it doesn't exist

import os
import logging
import argparse
import tools.filter
import tools.entropy
import tools.compress
import tools.utilityFunctions as util
# import tools.constants as constants


def clean_procedures(inputdir, options):
    logger.info("Starting filter procedures")
    specified_output = os.path.expanduser(options["output_path"]) if options["output_path"] is not None else None
    specified_output = util.remove_slash_from_path(specified_output)  # if slash exists
    change_output_location = specified_output is not None

    logger.debug("change output location: %s; specified output: %s" % (change_output_location, specified_output))
    filtered_suffix = "_filtered"
    if options['keep_time']:
        filtered_suffix += "_wtime"

    if not os.path.isdir(inputdir):
        outputdir_path = os.path.abspath(util.RUN_ISOLATED_FILES_PATH)
        if change_output_location:
            outputdir_path = os.path.abspath(specified_output)
    else:
        outputdir_path = inputdir + filtered_suffix
        if change_output_location:
            outputdir_path = os.path.join(os.path.abspath(specified_output),
                                          os.path.basename(inputdir) + filtered_suffix)
        filtered_suffix = None

    if not os.path.isdir(outputdir_path):
        logger.info("Creating directory %s" % outputdir_path)
        os.makedirs(outputdir_path)
    tools.filter.ds_filter(inputdir, outputdir_path, keep_time=options['keep_time'],
                           apply_limits=options['apply_limits'], round_to_int=options["round_to_int"],
                           hrf_col=abs(options["hrf-col"]), suffix=filtered_suffix)
    logger.info("Finished filter procedures")
    return


if __name__ == "__main__":

    # lets evaluate the directory for individual runs here
    if not os.path.exists(util.RUN_ISOLATED_FILES_PATH):
        os.mkdir(util.RUN_ISOLATED_FILES_PATH)

    # TODO: validate the input inside each module (to avoid unnecessary computation terminating in errors)
    parser = argparse.ArgumentParser(description="Filter all the files in the given directory")
    parser.add_argument("input_path", metavar="INPUT_PATH", nargs="+", action="store",
                        help="Path for a file(s) or directory containing the datasets to be used as input")
    tools.utilityFunctions.add_logger_parser_options(parser)
    tools.filter.add_parser_options(parser)
    tools.utilityFunctions.add_csv_parser_options(parser)
    args = parser.parse_args()
    options = vars(args)

    logger = util.initialize_logger(logger_name="tsanalyse", log_file=options["log_file"],
                                    log_level=options["log_level"], with_first_entry="TSFilter")

    # here we protect the execution for the case of sending multiple files as a string - required by other interfaces
    iterable_input_path = options['input_path'][0].split(" ") if len(options['input_path']) == 1 else options['input_path']

    for inputs in iterable_input_path:
        inputdir = inputs.strip()
        inputdir = util.remove_slash_from_path(inputdir)
        inputdir = os.path.expanduser(inputdir)  # to handle the case of paths as a string

        clean_procedures(inputdir, options)
        logger.info("Done.\n")
