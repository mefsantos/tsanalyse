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

       -lim, --apply-limits When filtering apply limit cutoffs (50<=hrf<=250)

       -kt, --keep-time     When cleaning keep both the hrf and the timestamp

       -rint, --round-to-int    Round the hrf values to int


Examples :

     Retrieve the hrf within the limits [50, 250]:
     ./TSAnalyseDirect.py unittest_dataset filter -lim

      Retrieve the timestamps and hrf
     ./TSAnalyseDirect.py unittest_dataset filter -kt


"""

# TODO: start using the output path given with the flag -o PATH. Also consider the remaining CSV optional arguments

import os
import logging
import argparse
import tools.filter
import tools.entropy
import tools.compress
import tools.utilityFunctions as util


def clean_procedures(inputdir, options):
    round_to_int = options["round_to_int"]
    logger.info("Starting filter procedures")
    if options['keep_time']:
        if not os.path.isdir(inputdir):
            outputdir = os.path.dirname(inputdir) + "_filtered_wtime"
        else:
            outputdir = inputdir + "_filtered"
        if not os.path.isdir(outputdir):
            logger.info("Creating directory %s" % outputdir)
            os.makedirs(outputdir)
        tools.filter.ds_filter(inputdir, outputdir, keep_time=True, apply_limits=options['apply_limits'],
                               round_to_int=round_to_int, hrf_col=options["hrf-col"])
    else:
        if not os.path.isdir(inputdir):
            outputdir = os.path.dirname(inputdir) + "_filtered"
        else:
            outputdir = inputdir + "_filtered"
        if not os.path.isdir(outputdir):
            logger.info("Creating filter directory %s" % outputdir)
            os.makedirs(outputdir)
        tools.filter.ds_filter(inputdir, outputdir, apply_limits=options['apply_limits'],
                               round_to_int=round_to_int, hrf_col=options["hrf-col"])
    logger.info("Finished filter procedures")
    return outputdir


if __name__ == "__main__":

    # lets evaluate the directory for individual runs here
    if not os.path.exists(util.RUN_ISOLATED_FILES_PATH):
        os.mkdir(util.RUN_ISOLATED_FILES_PATH)

    # TODO: validate the input inside each module (to avoid unnecessary computation terminating in errors)
    parser = argparse.ArgumentParser(description="Filter all the files in the given directory")
    parser.add_argument("inputdir", metavar="INPUT PATH", help="Path for a file or directory containing the datasets "
                                                               "to be used as input", action="store")
    parser.add_argument("--log", action="store", metavar="LOGFILE", default=None, dest="log_file",
                        help="Use LOGFILE to save logs.")
    parser.add_argument("--log-level", dest="log_level", action="store", help="Set Log Level; default:[%(default)s]",
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"], default="WARNING")

    tools.filter.add_parser_options(parser)
    tools.utilityFunctions.add_csv_parser_options(parser)
    args = parser.parse_args()
    options = vars(args)

    # Change this to a function and send it to tools to call in every file like:
    # init_logging(logger_name, logger_options)
    logger = logging.getLogger('tsanalyse')
    logger.setLevel(getattr(logging, options['log_level']))

    if options['log_file'] is None:
        log_output = logging.StreamHandler()
    else:
        log_output = logging.FileHandler(options['log_file'])

    log_output.setLevel(getattr(logging, options['log_level']))
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    log_output.setFormatter(formatter)
    logger.addHandler(log_output)
    # end of init_logger code -----------------------------------------------------

    inputdir = options['inputdir'].strip()
    inputdir = util.remove_slash_from_path(inputdir)  # if slash exists

    outputdir = clean_procedures(inputdir, options)

    if not os.path.isdir(inputdir):
        output_name = os.path.join(util.RUN_ISOLATED_FILES_PATH, os.path.basename(util.remove_file_extension(inputdir)))
    else:
        output_name = inputdir
