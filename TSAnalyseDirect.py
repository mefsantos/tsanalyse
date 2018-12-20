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


TSAnalyseDirect is a command line interface to apply operations
(compression, entropy, stv) from the tools module
directly to a file or files in a directory. The objective here is
to study the results of applying the compression or entropy directly on the files.

Usage: ./TSAnalyseDirect.py INPUT_DIRECTORY COMMAND COMMAND_OPTIONS

Common operations can be found in the examples section.

Four COMMANDS are available: filter, compress, entropy and stv.

It is assumed that when using compress or entropy the files only
contain the one column with the relevant information (hrf in our
case).

compress: This command allows you to compress all the files in the
    given directory. The list of available compressors is
    dynamically generated based on their availability in the system,
    below is the full list of all implemented compression algorithms.
    Unless changed the compression level used is always the max for
    the chosen algorithm (refer to the compressor's manual for this
    information).


    OUTCOME: Calling this command will create a csv file using ';'
    as a field delimiter. The compression algorithm and the
    compression level used are used to name the resulting file. This
    file will be created in the parent of the directory we are
    working with. Each file is represented by a row with three
    columns, the name of the file, it's original size and it's
    compressed size.

    COMMAND_OPTIONS for this command are:
    -c COMPRESSOR, --compressor COMPRESSOR
                        compression compressor to be used, available
                        compressors:paq8l, lzma, gzip, zip, bzip2, ppmd,
                        zlib, spbio;default:[paq8l]
    --level LEVEL       compression level to be used, this variable is
                        compressor dependent; default:[The maximum of whatever
                        compressor was chosen]
    -cr, --with-compression-ratio      Add an additional column with the compression ratio


entropy: This command allows you to calculate the entropy for all
    files in a given directory.

    OUTCOME: Calling this command will create a csv file using ';'
    as a field delimiter. The entropy measure and the
    compression level used are used to name the resulting file. This
    file will be created in the parent of the directory we are
    working with. Each file is represented by a row with two columns,
    the name of the file and it's entropy.


    COMMAND_OPTIONS are the available entropy measures:

    sampen              Sample Entropy
    apen                Approximate Entropy
    apenv2              A slightly different implementation of Approximate Entropy

    For a sampen and apen documentation please look at:
        pyeeg (http://code.google.com/p/pyeeg/downloads/list)

    All functions take arguments as inner options, to look at a
    particular entropy's options type:

    ./TSAnalyseDirect.py INPUT_DIRECTORY entropy ENTROPY -h


Examples :

  =>Compress
    Compress using the gzip algorithm (maximum compression level will be used)
        ./TSAnalyseDirect.py unittest_dataset compress -c gzip

    Compress using the bzip2 algorithm with minimum compression(1 in this case):
        ./TSAnalyseDirect.py unittest_dataset compress -c bzip2 --level 1


  =>Entropy
    Calculate the entropy using Approximate entropy with tolerance 0.2 and matrix
    dimension 2 (reference values for the analysis of biological data)
    ./TSAnalyseDirect.py unittest_dataset entropy apen -t 0.2

  =>stv
    Compress using the gzip algorithm (maximum compression level will be used)
        ./TSAnalyseDirect.py unittest_dataset stv

    Compress using the bzip2 algorithm with minimum compression(1 in this case):
        ./TSAnalyseDirect.py unittest_dataset compress -c bzip2 --level 1

"""

# TODO: add pydocs above regarding the new modules (stv analysis) and complete with the remaining optional params

# Mandatory imports
import os
import csv
import argparse
import tools.entropy
import tools.compress
import tools.stv_analysis as stv
import tools.utilityFunctions as util

if __name__ == "__main__":

    if not os.path.exists(util.RUN_ISOLATED_FILES_PATH):
        os.mkdir(util.RUN_ISOLATED_FILES_PATH)

    parser = argparse.ArgumentParser(description="Computes compression/entropy/short-term variability "
                                                 "of a file(s) or dataset(s)")
    parser.add_argument("input_path", metavar="INPUT PATH", action="store", nargs="+",
                        help="Path for a file(s) or directory containing the datasets to be used as input")

    tools.utilityFunctions.add_logger_parser_options(parser)
    tools.utilityFunctions.add_csv_parser_options(parser)
    # tools.utilityFunctions.add_dataset_parser_options(parser)

    subparsers = parser.add_subparsers(help='Different commands/operations to execute on the datasets', dest="command")

    compress = subparsers.add_parser('compress', help='Compress all the files in the given directory')
    tools.compress.add_parser_options(compress)
    tools.utilityFunctions.add_numbers_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='Calculate entropy for all the files in the given directory')
    tools.entropy.add_parser_options(entropy)
    tools.utilityFunctions.add_numbers_parser_options(entropy)

    # stv_module = subparsers.add_parser('stv', help='Perform Short-term Variability analysis of the files of a given '
    #                                                'directory with the following algorithms: %s'
    #                                                % stv.AVAILABLE_ALGORITHMS)
    # tools.stv_analysis.add_parser_options(stv_module)
    # tools.utilityFunctions.add_numbers_parser_options(stv_module)

    args = parser.parse_args()
    options = vars(args)
    # parser definition ends

    opts_to_protect = ["level", "dimension", "tolerance", "round_digits"]
    for option_key in opts_to_protect:
        if option_key in options.keys():
           options[option_key] = None if not options[option_key] else abs(options[option_key])
    #
    # options["dimension"] = abs(options["dimension"])
    # options["tolerance"] = abs(options["tolerance"])
    # options["round_digits"] = abs(options["round_digits"])

    logger = util.initialize_logger(logger_name="tsanalyse", log_file=options["log_file"],
                                    log_level=options["log_level"], with_first_entry="TSAnalyseDirect")

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
    iterable_input_path = options['input_path'][0].split(" ") if len(options['input_path']) == 1 else options[
        'input_path']

    # if the user specifies multiple files from different datasets (folders) we should create a tmp folder _
    # _ to hold all the files, and generate a name based on a timestamp (maybe add a parser flag)
    # _ default behaviour will group individual files into a temporary folder. (-i flag disables this)
    #  use this parser options: add_dataset_parser_options(parser, has_mult_files)

    # if files_are_relatable():
    # we create a temp dataset with their own parent dir name
    # OR: we always create a tmp folder to make things easy
    # keep_temp = options["keep_tmp_dir"]
    # temp_trial_dir = options["group_files_dir"]
    # isolate_files = options["isolate"]

    for inputs in iterable_input_path:
        inputdir = inputs.strip()
        inputdir = util.remove_slash_from_path(inputdir)
        inputdir = os.path.expanduser(inputdir)  # to handle the case of paths as a string

        if not os.path.isdir(inputdir):
            if change_output_location:
                single_run_on_specified_location = os.path.join(os.path.abspath(specified_output), "individual_runs")
                if not os.path.exists(single_run_on_specified_location):
                    logger.info("Creating directory '%s' for individual runs" % single_run_on_specified_location)
                    os.makedirs(single_run_on_specified_location)
                output_name = os.path.join(single_run_on_specified_location,
                                           os.path.basename(util.remove_file_extension(inputdir)))
            else:
                output_name = os.path.join(util.RUN_ISOLATED_FILES_PATH,
                                           os.path.basename(util.remove_file_extension(inputdir)))
        else:
            if change_output_location:
                output_name = os.path.join(os.path.abspath(specified_output), os.path.basename(inputdir))
            else:
                output_name = inputdir

        if options['command'] == 'compress':
            compressor = options['compressor']
            level = tools.compress.set_level(options)
            try:
                resulting_dict = tools.compress.compress(inputdir, compressor, level, False, options['comp_ratio'],
                                                     options['round_digits'])
            except OSError as ose:
                logger.critical("%s - %s" % (ose[1], util.remove_project_path_from_file(inputdir)))
            except IOError as ioe:
                logger.critical("%s - %s" % (ioe[1], util.remove_project_path_from_file(inputdir)))
            else:
                outfile = "%s_%s_lvl_%d" % (output_name, compressor, level)
                if options['comp_ratio']:
                    outfile += "_wCR"
                outfile += ".csv"

                if not tools.compress.is_compression_table_empty(resulting_dict):
                    logger.debug("Compression table: {0}".format(resulting_dict))
                    output_file = open(outfile, "w")
                    writer = csv.writer(output_file, delimiter=options["write_separator"],
                                        lineterminator=options["line_terminator"])
                    header = ["Filename", "Original_Size", "Compressed_Size"]
                    if options['comp_ratio']:
                        header.append("CRx100")

                    writer.writerow(header)

                    for filename in sorted(resulting_dict.keys()):
                        cd = resulting_dict[filename]
                        logger.debug("Compression Data for file '{1}': {0}".format(cd, filename))
                        data_row = [filename, cd.original, cd.compressed]
                        if options['comp_ratio']:
                            data_row.append(cd.compression_rate)

                        writer.writerow(data_row)
                    output_file.close()
                    logger.info("Storing in: %s" % os.path.abspath(outfile))
                else:
                    logger.warning("Compression table is empty. Nothing to write to file")

        elif options['command'] == 'entropy':
            algorithm = options["algorithm"]
            try:
                files_stds = tools.entropy.calculate_std(inputdir)
            except OSError as ose:
                logger.critical("%s - %s" % (ose[1], util.remove_project_path_from_file(inputdir)))
            except IOError as ioe:
                logger.critical("%s - %s" % (ioe[1], util.remove_project_path_from_file(inputdir)))

            else:
                tolerances = dict((filename, files_stds[filename] * options["tolerance"]) for filename in files_stds)
                logger.debug("Tolerances: %s" % tolerances)
                try:
                    resulting_dict = tools.entropy.entropy(inputdir, algorithm, options['dimension'], tolerances,
                                                           options['round_digits'])
                except OSError as ose:
                    logger.critical("%s - %s" % (ose[1], util.remove_project_path_from_file(inputdir)))
                except IOError as ioe:
                    logger.critical("%s - %s" % (ioe[1], util.remove_project_path_from_file(inputdir)))
                except ValueError as voe:
                    logger.critical("%s - %s" % (voe, util.remove_project_path_from_file(inputdir)))
                else:
                    outfile = "%s_%s_dim_%d_tol_%.2f.csv" % (
                        output_name, algorithm, options['dimension'], options['tolerance'])

                    if not tools.entropy.is_entropy_table_empty(resulting_dict):
                        output_file = open(outfile, "w")
                        writer = csv.writer(output_file, delimiter=options["write_separator"],
                                            lineterminator=options["line_terminator"])
                        writer.writerow(["Filename", "Entropy"])
                        logger.debug("Entropy table: %s" % resulting_dict)
                        for filename in sorted(resulting_dict.keys()):
                            entropyData = resulting_dict[filename]

                            logger.debug("Entropy Data for file '{1}': {0}".format(entropyData, filename))

                            writer.writerow([filename, entropyData.entropy])
                        output_file.close()
                        logger.info("Storing in: %s" % os.path.abspath(outfile))
                    else:
                        logger.warning("Entropy table is empty. Nothing to write to file")

        elif options['command'] == 'stv':
            try:
                tools.stv_analysis.compute_stv_metrics(inputdir, options)
            except OSError as ose:
                logger.critical("%s - %s" % (ose[1], util.remove_project_path_from_file(inputdir)))
            except IOError as ioe:
                logger.critical("%s - %s" % (ioe[1], util.remove_project_path_from_file(inputdir)))
            except ValueError as ve:
                logger.critical("%s" % ve)

    logger.info("Done")


