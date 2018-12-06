#!/usr/bin/python
# -*- coding: utf-8 -*-
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

TSAnalyseMultiScale is a command line interface to apply the multiscale method
based on (http://www.physionet.org/physiotools/mse/tutorial/), but using
compression also.

Usage:./TSAnalyseMultiScale.py [OPTIONS] INPUT COMMAND [COMMAND OPTIONS]

OPTIONS to apply when creating the scales:
  -start SCALE, --scale-start SCALE
                        Start scales with this amount of points. Default:[1]
  -stop SCALE, --scale-stop SCALE
                        Stop scales with this amount of points. Default:[20]
  -step STEP, --scale-step STEP
                        Step between every two scales.Default:[1]
  -mult MUL ORDER, --multiply-by-order MUL ORDER
                        Before calculating the resulting scale, multiply every
                        number in the series by MUL ORDER, -1 disables this
                        option; Default:[-1]
  -rint, --round-to-int Round the scales values to int.
  -ks, --keep-scales    After multiscale processing maintain the generated
                        scales

The two available commands are compress and entropy.

compress: This command allows you to compress all the files in the
     given directory.  The list of available compressors is
     dynamically generated based on their availability in the system,
     below is the full list of all implemented compression algorithms.
     Unless changed the compression level used is always the max for
     the chosen algorithm (refer to the compressor's manual for this
     information).


     OUTCOME: Calling this command will create a csv file using ';'
     as a field delimiter. The compression algorithm and the
     compression level used are used to name the resulting file. This
     file will be created in the parent of the directory we are
     working with. Each file is represented by a row with two
     columns per scale, it's original size and it's compressed size.

     COMMAND_OPTIONS for this command are:
     -c COMPRESSOR, --compressor COMPRESSOR
                        compression compressor to be used, available
                        compressors:paq8l, lzma, gzip, zip, bzip2, ppmd,
                        zlib, spbio;default:[paq8l]
     --level LEVEL      compression level to be used, this variable is
                        compressor dependent; default:[The maximum of whatever
                        compressor was chosen]
     # disabled --decompression    Use this option if you also wish to calculate how long it
                        takes to decompress the file once it's compressed
     -cr, --with-compression-ratio      Add an additional column with the compression ratio


entropy: This command allows you to calculate the entropy for all
     files in a given directory.

     OUTCOME: Calling this command will create a csv file using ';'
     as a field delimiter. The entropy measure and the
     compression level used are used to name the resulting file. This
     file will be created in the parent of the directory we are
     working with. Each file is represented by a row with one column per scale,
     it's entropy.


    COMMAND_OPTIONS are the available entropy measures:

     sampen              Sample Entropy
     apen                Approximate Entropy
     apenv2              A slightly different implementation of Approximate Entropy


    For a sampen and apen documentation please look at:
             pyeeg (http://code.google.com/p/pyeeg/downloads/list)

   All functions take arguments as inner options, to look at a
   particular entropy's options type:

   ./TSAnalyseMultiScale.py INPUT_DIRECTORY entropy ALGORITHM -h

Examples:

Multiscale entropy for all the files starting at scale 1(original files)
 and ending in scale 20
    ./TSAnalyseMultiScale.py unittest_dataset_filtered entropy sampen

Multiscale compression with rounded results for scale, since the scales are constructed
by averaging a given number of point we are bound to have floats, this options
rounds those numbers to an integer.
    ./TSAnalyseMultiScale.py unittest_dataset_filtered --round-to-int compress

Multiscale compression with rounded results for scale, multiplied by 10, the scale
point is multiplied by 10 and rounded. The final dataset also contains the compression ratio
    ./TSAnalyseMultiScale.py unittest_dataset_filtered --round-to-int --mult 10 compress -c paq8l -cr
"""

import os
import csv
import shutil
import logging
import argparse
import operator
import functools
import tools.entropy
import tools.compress
import tools.multiscale
import tools.utilityFunctions as util


def remove_scales_dir(scales, corrupted=False):
    message = "Cleaning up corrupted scales' directory (%s)..." % scales if corrupted \
        else "Cleaning up scales' directory (%s) ..." % scales
    logger.info(message)
    try:
        # os.removedirs(scales)
        shutil.rmtree(scales, ignore_errors=False)
    except OSError as err:
        logger.warning("%s (%s)" % (err[1], scales))
        logger.warning("skipping directory removal...")
    pass


if __name__ == "__main__":

    if not os.path.exists(util.RUN_ISOLATED_FILES_PATH):
        os.mkdir(util.RUN_ISOLATED_FILES_PATH)

    parser = argparse.ArgumentParser(description="Computes multiscale compression/entropy of a dataset")
    parser.add_argument("input_path", metavar="INPUT PATH", action="store", nargs="+",
                        help="Path for a file(s) or directory containing the dataset(s) to be used as input")
    tools.multiscale.add_parser_options(parser)
    tools.utilityFunctions.add_csv_parser_options(parser)
    tools.utilityFunctions.add_logger_parser_options(parser)

    subparsers = parser.add_subparsers(help='Different commands/operations to execute on the data sets', dest="command")

    compress = subparsers.add_parser("compress", help="use compression on multiscale")
    tools.compress.add_parser_options(compress)
    tools.utilityFunctions.add_numbers_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='Calculate multiscale entropy')
    tools.entropy.add_parser_options(entropy)
    tools.utilityFunctions.add_numbers_parser_options(entropy)

    args = parser.parse_args()
    options = vars(args)

    options["decompress"] = None  # decompress is disabled. This os the shortest mod without deleting code

    logger = util.initialize_logger(logger_name="tsanalyse", log_file=options["log_file"],
                                    log_level=options["log_level"], with_first_entry="TSAnalyseMultiScale")

    change_output_location = False
    specified_output = os.path.expanduser(options["output_path"]) if options["output_path"] is not None else None
    specified_output = util.remove_slash_from_path(specified_output)  # if slash exists

    if specified_output is not None:
        if os.path.exists(specified_output):
            logger.info("Using specified output destination.")
            specified_output = os.path.abspath(specified_output)
            change_output_location = True
        else:
            logger.warning("Specified folder '%s' does not exist. Ignoring..." % os.path.abspath(specified_output))

    # here we protect the execution for the case of sending multiple files as a string - required by other interfaces
    iterable_input_path = options['input_path'][0].split(" ") if len(options['input_path']) == 1 else options['input_path']

    for inputs in iterable_input_path:
        input_dir = inputs.strip()
        input_dir = util.remove_slash_from_path(input_dir)  # if slash exists
        input_dir = os.path.expanduser(input_dir)  # to handle the case of paths as a string

        scales_dir = '%s_Scales' % (input_dir if os.path.isdir(input_dir)
                                    else os.path.join(util.RUN_ISOLATED_FILES_PATH,
                                                      os.path.basename(util.remove_file_extension(input_dir))))

        scales_dir = os.path.abspath(scales_dir)

        if options['round']:
            scales_dir += "_int"
        if options['mul_order'] != -1:
            scales_dir += '_%d' % (options['mul_order'])

        if options["scale_step"] == 0:
            logger.warning("Step value cannot be 0 (current: %s). Falling back to the minimum acceptable (1)."
                           % options["scale_step"])
            options["scale_step"] = 1

        logger.info("Creating Scales directory")

        try:
            tools.multiscale.create_scales(input_dir, scales_dir, options["scale_start"], options["scale_stop"] + 1,
                                           options["scale_step"], options['mul_order'], options['round'])
        except OSError as ose:
            logger.critical("%s - %s" % (ose[1], input_dir))
            remove_scales_dir(scales_dir, corrupted=True)
        except IOError as ioe:
                logger.critical("%s - %s" % (ioe[1], input_dir))
                remove_scales_dir(scales_dir, corrupted=True)
        except ValueError as error:
            logger.critical("%s. Did you forget to filter the file?" % error)
            remove_scales_dir(scales_dir, corrupted=True)
        else:
            logger.info("Scales Directory created")

            if not os.path.isdir(input_dir):
                if change_output_location:
                    single_run_on_specified_location = os.path.join(os.path.abspath(specified_output), "individual_runs")
                    if not os.path.exists(single_run_on_specified_location):
                        logger.info("Creating directory '%s' for individual runs" % single_run_on_specified_location)
                        os.makedirs(single_run_on_specified_location)
                    output_name = os.path.join(single_run_on_specified_location,
                                               os.path.basename(util.remove_file_extension(input_dir)))
                else:
                    output_name = os.path.join(util.RUN_ISOLATED_FILES_PATH,
                                               os.path.basename(util.remove_file_extension(input_dir)))
            else:
                if change_output_location:
                    output_name = os.path.join(os.path.abspath(specified_output), os.path.basename(input_dir))
                else:
                    output_name = input_dir

            if options["command"] == "compress":
                options["level"] = tools.compress.set_level(options)
                if options['decompress']:
                    outfile = "%s_multiscale_start_%d_end_%d_step_%d_decompress_%s_lvl_%s" % (
                        output_name, options["scale_start"], options["scale_stop"], options["scale_step"], options["compressor"],
                        options["level"])
                else:
                    outfile = "%s_multiscale_start_%d_end_%d_step_%d_%s_lvl_%s" % (
                        output_name, options["scale_start"], options["scale_stop"], options["scale_step"], options["compressor"],
                        options["level"])
                if options['round']:
                    outfile += "_int"
                if options['mul_order'] != -1:
                    outfile += "_%d" % (options["mul_order"])
                if options['comp_ratio']:
                    outfile += "_wCR"
                outfile += ".csv"

                try:
                    compression_table = tools.multiscale.multiscale_compression(input_dir, scales_dir, options["scale_start"],
                                                                            options["scale_stop"] + 1, options["scale_step"],
                                                                            options["compressor"], options["level"],
                                                                            options["decompress"], options["comp_ratio"],
                                                                            options['round_digits'])
                except OSError as ose:
                    logger.critical("%s - %s" % (ose[1], input_dir))
                    remove_scales_dir(scales_dir, corrupted=True)
                except IOError as ioe:
                    logger.critical("%s - %s" % (ioe[1], input_dir))
                    remove_scales_dir(scales_dir, corrupted=True)
                else:
                    if not tools.compress.is_compression_table_empty(compression_table):

                        output_file = open(outfile, "w")
                        writer = csv.writer(output_file, delimiter=options["write_separator"], lineterminator=options["line_terminator"])

                        if (not options['decompress']) and (not options['comp_ratio']):
                            header = ["Filename"] + list(functools.reduce(
                                operator.add, [("Scale_%d_Original" % s, "Scale_%d_Compressed" % s)
                                               for s in range(options["scale_start"],
                                                              options["scale_stop"] + 1,
                                                              options["scale_step"])]))
                        elif options['decompress'] and (not options['comp_ratio']):
                            header = ["Filename"] + list(
                                functools.reduce(
                                    operator.add, [("Scale_%d_Original" % s, "Scale_%d_Compressed" % s, "Scale_%d_Decompression" % s)
                                                   for s in range(options["scale_start"],
                                                                  options["scale_stop"] + 1,
                                                                  options["scale_step"])]))

                        elif (not options['decompress']) and options['comp_ratio']:
                            header = ["Filename"] + list(functools.reduce(
                                operator.add, [("Scale_%d_Original" % s,"Scale_%d_Compressed" % s, "Scale_%d_CRx100" % s)
                                               for s in range(options["scale_start"],
                                                              options["scale_stop"] + 1,
                                                              options["scale_step"])]))
                        else:
                            header = ["Filename"] + list(
                                functools.reduce(
                                    operator.add, [("Scale_%d_Original" % s,
                                                    "Scale_%d_Compressed" % s,
                                                    "Scale_%d_CRx100" % s,
                                                    "Scale_%d_Decompression" % s)
                                                   for s in range(options["scale_start"],
                                                                  options["scale_stop"] + 1,
                                                                  options["scale_step"])]))

                        writer.writerow(header)
                        for filename in sorted(compression_table.keys()):

                            if len(compression_table[filename]) > 0:
                                writer.writerow([filename] + compression_table[filename])

                        output_file.close()
                        logger.info("Storing in: %s" % os.path.abspath(outfile))

                    else:
                        logger.warning("Compression table is empty. Nothing to write to file")

            elif options["command"] == "entropy":
                algorithm = options['algorithm']
                if algorithm == 'apen' or algorithm == 'apenv2' or algorithm == "sampen":
                    outfile = "%s_multiscale_start_%d_end_%d_step_%d_%s_dim_%d_tol_%.2f.csv" % (output_name,
                                                                                                options["scale_start"],
                                                                                                options["scale_stop"],
                                                                                                options["scale_step"],
                                                                                                algorithm,
                                                                                                options["dimension"],
                                                                                                options["tolerance"])
                    entropy_table = {}

                    try:
                        entropy_table = tools.multiscale.multiscale_entropy(input_dir, scales_dir,
                                                                        options["scale_start"], options["scale_stop"] + 1,
                                                                        options["scale_step"], algorithm,
                                                                        options["dimension"], options["tolerance"],
                                                                        options["round_digits"])
                    except OSError as ose:
                        logger.critical("%s - %s" % (ose[1], input_dir))
                        remove_scales_dir(scales_dir, corrupted=True)
                    except IOError as ioe:
                        logger.critical("%s - %s" % (ioe[1], input_dir))
                        remove_scales_dir(scales_dir, corrupted=True)
                    else:
                        if not tools.entropy.is_entropy_table_empty(entropy_table):
                            output_file = open(outfile, "w")
                            writer = csv.writer(output_file, delimiter=options["write_separator"],
                                                lineterminator=options["line_terminator"])

                            header = ["Filename"] + ["Scale_%d_Entropy" % s for s in
                                                     range(options["scale_start"], options["scale_stop"] + 1,
                                                           options["scale_step"])]
                            writer.writerow(header)
                            for filename in sorted(entropy_table.keys()):

                                if len(entropy_table[filename]) > 0:
                                    writer.writerow([filename] + entropy_table[filename])

                            output_file.close()
                            logger.info("Storing in: %s" % os.path.abspath(outfile))
                        else:
                            logger.warning("Entropy table is empty. Nothing to write to file")

                else:
                    logger.error("Multiscale not implemented for %s" % algorithm)
                    remove_scales_dir(scales_dir)

            if not options["keep_scales"]:
                # logger.info("Deleting scales directory: %s" % scales_dir)
                remove_scales_dir(scales_dir)

    logger.info("Done")
