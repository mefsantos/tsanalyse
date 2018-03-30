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
  --multiply MUL ORDER  before calculating the resulting scale, multiply every
                        number in the series by MUL ORDER, -1 disables this
                        option; Default:[-1]
  --round-to-int

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
     --decompression    Use this option if you also wish to calculate how long it
                        takes to decompress the file once it's compressed


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
     apenv2              A slightly different implementation of Aproximate Entropy


    For a sampen and apen documentation please look at:
             pyeeg (http://code.google.com/p/pyeeg/downloads/list)

   All functions take arguments as inner options, to look at a
   particular entropy's options type:

   ./TSAnalyseMultiScale.py INPUT_DIRECTORY entropy ENTROPY -h

Examples:

Multiscale entropy for all the files starting at scale 1(original files)
 and ending in scale 20
./TSAnalyseMultiScale.py unittest_dataset entropy sampen

Multiscale compression with rounded results for scale, since the scales are constructed
by averaging a given number of point we are bound to have floats, this options
rounds those numbers to an integer.
./TSAnalyseMultiScale.py unittest_dataset --round-to-int compress

Multiscale compression with rounded results for scale, multiplied by 10, the scale
point is multiplied by 10 and rounded.
./TSAnalyseMultiScale.py unittest_dataset --round-to-int --multiply 10 compress -c paq8l

Compression Ratio
./TSAnalyseMultiScale.py ../Datasets/Compression_Results/ cr

Confidence Intervals with Slope Analysis:
./TSAnalyseMultiScale.py ../Datasets/Entropy_DS/MultiScale cisa -mo

"""

import os
import csv
import logging
import argparse
import operator
import functools
import tools.entropy
import tools.compress
import tools.multiscale
import tools.utilityFunctions as util


# Flag to control argparser based on the imports
import_logger = logging.getLogger('tsanalyse')
import_logger.info(" ###### Imports: ###### ")

cr_exists = False
cisa_exists = False

try:
    import tools.compressionRatio as compratio
    cr_exists = True
except ImportError:
    import_logger.info("Missing module: compressionRatio. Ignoring...")

try:
    import tools.confidenceIntervalWithSlopeAnalysis as cisa
    cisa_exists = True
except ImportError:
    import_logger.info("Missing module: confidenceIntervalWithSlopeAnalysis. Ignoring...")

import_logger.info(" ###################### ")


if __name__ == "__main__":

    # lets evaluate the directory for individual runs here
    if not os.path.exists(util.RUN_ISOLATED_FILES_PATH):
        os.mkdir(util.RUN_ISOLATED_FILES_PATH)

    parser = argparse.ArgumentParser(description="Generates a tables of file multiscaled compression/entropy")
    parser.add_argument("inputdir", metavar="INPUT DIRECTORY", help="Directory to be used as input")
    parser.add_argument("--log", action="store", metavar="LOGFILE", default=None, dest="log_file",
                        help="Use LOGFILE to save logs.")
    parser.add_argument("--log-level", dest="log_level", action="store", help="Set Log Level; default:[%(default)s]",
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"], default="WARNING")

    tools.multiscale.add_parser_options(parser)

    subparsers = parser.add_subparsers(help='Different commands/operations to execute on the data sets', dest="command")

    compress = subparsers.add_parser("compress", help="use compression on multiscale")
    tools.compress.add_parser_options(compress)
    tools.utilityFunctions.add_csv_parser_options(compress)
    tools.utilityFunctions.add_numbers_parser_options(compress)

    entropy = subparsers.add_parser("entropy", help="use entropy on multiscale")

    tools.entropy.add_parser_options(entropy)

    # 28/02/18 - removed flags to avoid excessive unexplained functionalities (paper review)
    # if cr_exists:
    #     comp_ratio = subparsers.add_parser('comp_ratio',
    #                                        help='Compute the compression Rate and Confidence Interval of the a given '
    #                                             'dataset. Receives a dataset (file or folder) with the compression '
    #                                             'result and calculate both the compression ratio and the confidence '
    #                                             'interval, generating new datasets with the computed metrics appended.')
    #     tools.utilityFunctions.add_csv_parser_options(comp_ratio)
    #     cr = subparsers.add_parser('cr', help='Execute comp_ratio command')
    #     tools.utilityFunctions.add_csv_parser_options(cr)

    # import try/catch not working properly - commented to disable these commands to be displayed
    # if cisa_exists:
    #     confidence_interval = subparsers.add_parser('confidence_interval_slope_analysis',
    #                                                 help='Compute the Confidence Interval for each scale (uniscale or '
    #                                                      'multiscale). Receives a dataset (ex: entropy results), '
    #                                                      'calculate the confidence interval and generates a new '
    #                                                      'dataset with the metrics appended.')
    #     cisa.add_parser_options(confidence_interval)
    #     tools.utilityFunctions.add_csv_parser_options(confidence_interval)
    #
    #     conf_int = subparsers.add_parser('cisa', help='Execute confidence_interval_slope_analysis command')
    #     cisa.add_parser_options(conf_int)
    #     tools.utilityFunctions.add_csv_parser_options(conf_int)

    args = parser.parse_args()
    options = vars(args)

    # parser definition ends

    options["decompress"] = None  # decompress is disabled. This os the shortest mod without deleting code

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

    input_dir = options['inputdir'].strip()

    input_dir = util.remove_slash_from_path(input_dir)  # if slash exists

    # compute multiscales
    if options['command'] not in ["comp_ratio", "cr", "confidence_interval_slope_analysis", "cisa"]:
        # add exception in case we try to run a single file and not a directory
        scales_dir = '%s_Scales' % (input_dir if os.path.isdir(input_dir)
                                    else os.path.join(util.RUN_ISOLATED_FILES_PATH,
                                                      os.path.basename(util.remove_file_extension(input_dir))))

        if options['round']:
            scales_dir += "_int"
        if options['mul_order'] != -1:
            scales_dir += '_%d' % (options['mul_order'])

        logger.info("Creating Scales Directory")

        # TODO: start using a specific directory for the outputs
        tools.multiscale.create_scales(input_dir, scales_dir, options["scale_start"], options["scale_stop"] + 1,
                                       options["scale_step"], options['mul_order'], options['round'])
        logger.info("Scales Directory created")

        if not os.path.isdir(input_dir):
            # output_name = "%s_%s" % (os.path.split(inputdir)[0], os.path.basename(inputdir))
            output_name = os.path.join(util.RUN_ISOLATED_FILES_PATH,
                                       os.path.basename(util.remove_file_extension(input_dir)))
            # if we are just evaluating a file we will place it in RUN_ISOLATED_FILES_PATH with its original name without
            # the csv. the rest of the name will be added depending on the operation
        else:
            output_name = input_dir

        # TODO : CONTINUAR A DEFINIR OUTPUT_NAME COMO NOME DO FICHEIRO A GRAVAR

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

            compression_table = tools.multiscale.multiscale_compression(input_dir, scales_dir, options["scale_start"],
                                                                        options["scale_stop"] + 1, options["scale_step"],
                                                                        options["compressor"], options["level"],
                                                                        options["decompress"], options["comp_ratio"],
                                                                        options['round_digits'])

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
                writer.writerow([filename] + compression_table[filename])

            output_file.close()
            print("Storing into: %s" % os.path.abspath(outfile))

        elif options["command"] == "entropy":
            if options['entropy'] == 'apen' or options['entropy'] == 'apenv2' or options['entropy'] == "sampen":
                outfile = "%s_multiscale_start_%d_end_%d_step_%d_%s_dim_%d_tol_%.2f.csv" % (output_name,
                                                                                            options["scale_start"],
                                                                                            options["scale_stop"],
                                                                                            options["scale_step"],
                                                                                            options["entropy"],
                                                                                            options["dimension"],
                                                                                            options["tolerance"])

                entropy_table = {}

                entropy_table = tools.multiscale.multiscale_entropy(input_dir, scales_dir,
                                                                    options["scale_start"], options["scale_stop"] + 1,
                                                                    options["scale_step"], options["entropy"],
                                                                    options["dimension"], options["tolerance"])

                output_file = open(outfile, "w")
                writer = csv.writer(output_file, delimiter=";")

                header = ["Filename"] + ["Scale_%d_Entropy" % s for s in
                                         range(options["scale_start"], options["scale_stop"] + 1, options["scale_step"])]
                writer.writerow(header)
                for filename in sorted(entropy_table.keys()):
                    writer.writerow([filename] + entropy_table[filename])

                output_file.close()
                print("Storing into: %s" % os.path.abspath(outfile))
                # logger.info("Storing into: %s" % os.path.abspath(outfile))

            else:
                logger.error("Multiscale not implemented for %s" % options["entropy"])

    # the following commands are disabled
    # else:   # command doesn't need to compute multiscale
    #     read_sep, write_sep, line_term = options['read_separator'], options['write_separator'], options['line_terminator']
    #
    #     if options['round_digits'] is not None:
    #         round_digits = int(options['round_digits'])
    #     else:
    #         round_digits = None
    #
    #     inputdir = input_dir
    #     if options['command'] == 'comp_ratio' or options['command'] == 'cr':
    #         if os.path.isfile(inputdir):
    #             compratio.compression_ratio_from_file(inputdir, round_digits=round_digits, sep2read=read_sep,
    #                                            sep2write=write_sep, line_term=line_term)
    #         else:
    #             compratio.compression_ratio_from_dir(inputdir, round_digits=round_digits, sep2read=read_sep,
    #                                           sep2write=write_sep, line_term=line_term)
    #
    #     elif options['command'] == 'confidence_interval_slope_analysis' or options['command'] == 'cisa':
    #         util.DEBUG = options['debug_mode']
    #         if os.path.isfile(inputdir):
    #                 cisa.confidence_intervals_with_slope_analysis_from_file(inputdir, round_digits=round_digits,
    #                                                                         sep2read=read_sep, sep2write=write_sep,
    #                                                                         line_term=line_term,
    #                                                                         no_slope_analysis_flag=options['no_slope_analysis'])
    #         else:
    #             metrics_output_path = util.remove_slash_from_path(options['output_path'])
    #             cisa.confidence_intervals_with_slope_analysis_from_dir(inputdir,
    #                                                                    single_dataset_flag=options['single_dataset'],
    #                                                                    metrics_output_path= metrics_output_path,
    #                                                                    round_digits=options['round_digits'],
    #                                                                    sep2read=read_sep, sep2write=write_sep,
    #                                                                    line_term=line_term,
    #                                                                    no_slope_analysis_flag=options['no_slope_analysis'])
