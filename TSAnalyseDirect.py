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
(compression, entropy, filter, partition) from the tools module
directly to a file or files in a directory. The objective here is
to study the results of applying the compression or entropy directly on the files.

Usage: ./TSAnalyseDirect.py INPUT_DIRECTORY COMMAND COMMAND_OPTIONS

Common operations can be found in the examples section.

Four COMMANDS are available: filter, compress, entropy and stv.

It is assumed that when using compress or entropy the files only
contain the one column with the relevant information (hrf in our
case).

filter: This command allows you to apply filter and partitioning
      operations. Cleaning a file means extracting the heart rate
      frequencies (timestamps may also be saved).  Partitioning cuts
      the file according to a given interval. Note that partitions
      starting at the end of file will generate files where the data
      is inverted.

      OUTCOME: Calling this command will create a new directory with a
      _clean appended to the original directory's name were all the
      filter files are saved (this directory is created whether you
      call this interface on a directory or file).

      COMMAND_OPTIONS for this command are:

       -lim, --apply-limits When filtering apply limit cutoffs (50<=hrf<=250)

       -kt, --keep-time     When cleaning keep both the hrf and the timestamp

       -ds SECONDS, --deferred-start SECONDS
                        Time gap between the start of the file and the start
                        of the interval; default:[0]

       -ul, --use-lines         Partition using line count instead of time
       -rint, --round-to-int    Round the hrf values to int


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
     --level LEVEL      compression level to be used, this variable is
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


  =>Filter:
     Retrieve the hrf:
     ./TSAnalyseDirect.py unittest_dataset filter

      Retrieve the timestamps and hrf
     ./TSAnalyseDirect.py unittest_dataset filter -kt

     Retrieve the valid hrf(50<=hrf<=250) for the last hour:
     ./TSAnalyseDirect.py unittest_dataset filter -s 3600 --apply-limits

     discards the first 30 seconds of recordings and retrieve the remaining hrf data
     ./TSAnalyseDirect.py unittest_dataset filter -ds 30

     Retrieve the hrf from first 2000 lines:
     ./TSAnalyseDirect.py unittest_dataset filter -s 2000 --use-lines


  =>Compress
     Compress using the gzip algorithm (maximum compression level will be used)
         ./TSAnalyseDirect.py unittest_dataset compress -c gzip

     Compress using the bzip2 algorithm with minimum compression(1 in this case):
     ./TSAnalyseDirect.py unittest_dataset compress -c bzip2 --level 1


  =>Entropy
     Calculate the entropy using Approximate entropy with tolerance 0.2 and matrix
      dimension 2 (reference values for the analysis of biological data)
     ./TSAnalyseDirect.py unittest_dataset entropy apen -t 0.2

"""

# TODO: add pydocs above regarding the new modules (stv analysis) and complete with the remaining optional params

# Mandatory imports
import os
import csv
import logging
import argparse
import tools.filter
import tools.entropy
import tools.compress
import tools.partition
import tools.stv_analysis as stv
import tools.utilityFunctions as util

# Flag to control argparser based on the imports
import_logger = logging.getLogger('tsanalyse')
import_logger.info(" ###### Imports: ###### ")

csv2txsp3_exists = False
recordDuration_exists = False
fma_exists = False
csa_exists = False
dsduration_exists = False

# under development / unnecessary tools
# try:
#     import tools.csv2txsp3
#     csv2txsp3_exists = True
# except ImportError:
#     #  module missing - gitIgnore
#     import_logger.info("Missing module: csv2txsp3. Ignoring...")

# try:
#     import tools.recordDuration
#     recordDuration_exists = True
# except ImportError:
#     #  module missing - gitIgnore
#     import_logger.info("Missing module: recordDuration. Ignoring...")
#
# try:
#     import tools.fetalMaturationAnalysis
#     fma_exists = True
# except ImportError:
#     #  module missing - gitIgnore
#     import_logger.info("Missing module: fetalMaturationAnalysis. Ignoring...")
#
# try:
#     import tools.clampStateAnalysis
#     csa_exists = True
# except ImportError:
#     #  module missing - gitIgnore
#     import_logger.info("Missing module: clampStateAnalysis. Ignoring...")
#
# try:
#     import tools.durationFromSingleDS as dsd
#     dsduration_exists = True
# except ImportError:
#     #  module missing - gitIgnore
#     import_logger.info("Missing module: durationFromSingleDS. Ignoring...")

import_logger.info(" ###################### ")


def partition_procedures(inputdir, options):
    if options['start_at_end']:
        outputdir = "%s_last_%d_%d" % (inputdir, options['partition_start'], options['section'])
    else:
        outputdir = "%s_%d_%d" % (inputdir, options['partition_start'], options['section'])

    if not os.path.isdir(outputdir):
        logger.info("Creating %s for partitions" % outputdir)
        os.makedirs(outputdir)
    logger.info("Starting partition")
    tools.partition.partition(inputdir,
                              outputdir,
                              options['partition_start'],
                              options['section'],
                              options['gap'],
                              options['start_at_end'],
                              options['full_file'],
                              options['using_lines'])
    logger.info("Finished partitioning")
    return outputdir


def clean_procedures(inputdir, options):
    round_to_int = options["round_to_int"]
    logger.info("Starting filter procedures")
    if options['keep_time'] or options['section']:
        if not os.path.isdir(inputdir):
            outputdir = os.path.dirname(inputdir) + "_filtered_wtime"
        else:
            outputdir = inputdir + "_filtered"
        if not os.path.isdir(outputdir):
            logger.info("Creating partition directory %s" % outputdir)
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


def set_disabled_parser_options_values(parser_args, parser_options):
    # filter
    if not hasattr(parser_args, "start_at_end"):
        parser_options["start_at_end"] = False
    if not hasattr(parser_args, "section"):
        parser_options["section"] = None
    if not hasattr(parser_args, "gap"):
        parser_options["gap"] = None
    if not hasattr(parser_args, "full_file"):
        parser_options["full_file"] = True

if __name__ == "__main__":

    # lets evaluate the directory for individual runs here
    if not os.path.exists(util.RUN_ISOLATED_FILES_PATH):
        os.mkdir(util.RUN_ISOLATED_FILES_PATH)

    # TODO: validate the input inside each module (to avoid unnecessary computation terminating in errors)
    parser = argparse.ArgumentParser(description="Generates a table of file compression/entropy and new datasets "
                                                 "(when needed) for a given file or directory")
    parser.add_argument("inputdir", metavar="INPUT PATH", help="Path for a file or directory containing the datasets "
                                                               "to be used as input", action="store")
    parser.add_argument("--log", action="store", metavar="LOGFILE", default=None, dest="log_file",
                        help="Use LOGFILE to save logs.")
    parser.add_argument("--log-level", dest="log_level", action="store", help="Set Log Level; default:[%(default)s]",
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"], default="WARNING")

    subparsers = parser.add_subparsers(help='Different commands/operations to execute on the data sets', dest="command")

    ds_filter = subparsers.add_parser('filter', help='Filter all the files in the given directory')
    tools.filter.add_parser_options(ds_filter)
    tools.partition.add_parser_options(ds_filter, full_file_option=True)
    tools.utilityFunctions.add_csv_parser_options(ds_filter)

    compress = subparsers.add_parser('compress', help='Compress all the files in the given directory')
    tools.compress.add_parser_options(compress)
    tools.utilityFunctions.add_csv_parser_options(compress)
    tools.utilityFunctions.add_numbers_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='Calculate entropy for all the files in the given directory')
    tools.entropy.add_parser_options(entropy)

    # import try/catch not working properly - commented to disable these commands to be displayed
    # if dsduration_exists:
    #     dsduration = subparsers.add_parser('duration',
    #                                        help='Calculate the duration of recordings for all the files in the given directory')
    # if csv2txsp3_exists:
    #     sisporto = subparsers.add_parser('sisporto_format',
    #                                      help='Transform csv-like files into sisporto TxSP3 format files')
    #
    # if csa_exists:
    #     clamp_analysis = subparsers.add_parser('clamp_analysis',
    #                                            help='Computes the entropy and compression for PIAS, PIAD and PIAM '
    #                                                 'for the given datasets. Also enables the division of the dataset '
    #                                                 'by state and storing intermediary data sets.')
    #
    #     tools.utilityFunctions.add_csv_parser_options(clamp_analysis)
    #     tools.compress.add_parser_options(clamp_analysis)
    #     tools.entropy.add_parser_options(clamp_analysis)
    #     tools.clampStateAnalysis.add_parser_options(clamp_analysis)
    #
    #     ca = subparsers.add_parser('ca', help='Executes clamp_analysis command')
    #     tools.utilityFunctions.add_csv_parser_options(ca)
    #     tools.compress.add_parser_options(ca)
    #     tools.entropy.add_parser_options(ca)
    #     tools.clampStateAnalysis.add_parser_options(ca)
    #
    # if fma_exists:
    #     longit_base_analysis = subparsers.add_parser('maturation',
    #                                                  help='Compute the confidence intervals for the longitudinal base '
    #                                                       'dataset.')
    #     tools.fetalMaturationAnalysis.add_parser_options(longit_base_analysis)
    #     tools.utilityFunctions.add_csv_parser_options(longit_base_analysis)
    #
    #     fma = subparsers.add_parser('fma', help='Execute maturation command')
    #     tools.fetalMaturationAnalysis.add_parser_options(fma)
    #     tools.utilityFunctions.add_csv_parser_options(fma)

    # if dsduration_exists:
    #     singleRun = subparsers.add_parser('clean_duration', help='DS Duration after cleaning file')

    stv = subparsers.add_parser('stv', help='Perform Short-term Variability analysis with the following algorithms: '
                                            '%s' % stv.AVAILABLE_ALGORITHMS)
    tools.stv_analysis.add_parser_options(stv)
    tools.utilityFunctions.add_csv_parser_options(stv)

    args = parser.parse_args()
    options = vars(args)

    # parser definition ends

    # disabled filter parser options:
    set_disabled_parser_options_values(args, options)

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

    # TODO: later we might remove this when every command accepts these flags
    # Global options for csv's
    read_sep = options['read_separator'] if hasattr(args, "read_separator") else ";"
    write_sep = options['write_separator'] if hasattr(args, "write_separator") else ";"
    line_term = options['line_terminator'] if hasattr(args, "line_terminator") else "\n"

    round_digits = options['round_digits'] if hasattr(args, "round_digits") else None
    round_digits = int(round_digits) if round_digits is not None else None

    inputdir = options['inputdir'].strip()
    inputdir = util.remove_slash_from_path(inputdir)  # if slash exists

    # TODO: move the filter command to be an individual interface
    if options['command'] == 'filter':
        outputdir = clean_procedures(inputdir, options)
        if options['section']:
            outputdir = partition_procedures(outputdir, options)
        inputdir = outputdir

    if not os.path.isdir(inputdir):
        output_name = os.path.join(util.RUN_ISOLATED_FILES_PATH, os.path.basename(util.remove_file_extension(inputdir)))
    else:
        output_name = inputdir

    if options['command'] == 'compress':
        compressor = options['compressor']
        level = tools.compress.set_level(options)
        resulting_dict = tools.compress.compress(inputdir, compressor, level, False,
                                                 options['comp_ratio'], round_digits)

        # if options['decompress']:
        # #     outfile = "%s_decompress_%s_%d" % (output_name, compressor, level)
        # else:
        outfile = "%s_%s_lvl_%d" % (output_name, compressor, level)
        if options['comp_ratio']:
            outfile += "_wCR"
        outfile += ".csv"

        output_file = open(outfile, "w")
        writer = csv.writer(output_file, delimiter=options["write_separator"], lineterminator=options["line_terminator"])
        header = ["Filename", "Original_Size", "Compressed_Size"]
        if options['comp_ratio']:
            header.append("CRx100")
        # if options['decompress']:
        #     header.append("Decompression_Time")
        writer.writerow(header)

        for filename in sorted(resulting_dict.keys()):
            cd = resulting_dict[filename]
            # data_row = [filename, cd.original, cd.compression_rate, cd.compressed]
            data_row = [filename, cd.original, cd.compressed]
            if options['comp_ratio']:
                data_row.append(cd.compression_rate)
            # else:
            #   del (data_row[2])
            # if options['decompress']:
            #     data_row.append(cd.time)
            writer.writerow(data_row)
        output_file.close()
        print("Storing into: %s" % os.path.abspath(outfile))

    elif options['command'] == 'entropy':
        files_stds = tools.entropy.calculate_std(inputdir)
        tolerances = dict((filename, files_stds[filename] * options["tolerance"]) for filename in files_stds)

        resulting_dict = tools.entropy.entropy(inputdir,
                                               options['entropy'],
                                               options['dimension'],
                                               tolerances, round_digits)

        outfile = "%s_%s_dim_%d_tol_%.2f.csv" % (output_name, options['entropy'],
                                                 options['dimension'], options['tolerance'])
        output_file = open(outfile, "w")
        writer = csv.writer(output_file, delimiter=";")
        writer.writerow(["Filename", "Entropy"])
        for filename in sorted(resulting_dict.keys()):
            entropyData = resulting_dict[filename]
            writer.writerow([filename, entropyData.entropy])
        output_file.close()
        print("Storing into: %s" % os.path.abspath(outfile))

    elif options['command'] == 'stv':
        tools.stv_analysis.compute_stv_metric_of_directory(inputdir, options['algorithm'],
                                                           options['sampling_frequency'],
                                                           output_path=options["output_path"])

    # The following commands are disabled
    # elif options['command'] == 'duration':
    #     # add option to define the file separator to use
    #     # default is ";"
    #     output_dir = os.path.abspath(".")
    #     tools.recordDuration.parse_input_path(inputdir, output_dir)
    #
    # elif options['command'] == 'sisporto_format':
    #     # add option to define the file separator to use
    #     # default is space ("\s")  - to read and to write
    #     tools.csv2txsp3.parse_input_path(inputdir)
    #
    # elif options['command'] == 'clamp_analysis' or options['command'] == 'ca':
    #     input_is = "dir"
    #     compressor = options['compressor']
    #     level = tools.compress.set_level(options)
    #     if os.path.isfile(inputdir):
    #         input_is = "file"
    #     method_2_call = getattr(sys.modules[tools.clampStateAnalysis.__name__], "clamp_analysis_from_%s" % input_is)
    #
    #     method_2_call(input_path=inputdir, entropy_2_use=options['entropy'],
    #                   entropy_tolerance=options['tolerance'], entropy_dimension=options['dimension'],
    #                   compressor_2_use=compressor, compressor_level=level,
    #                   with_compression_ratio=options["compression_ratio"],
    #                   sep2read=read_sep, sep2write=write_sep, line_term=line_term,
    #                   store_by_state=options['store_by_state'],
    #                   output_path=util.remove_slash_from_path(options['output_path']),
    #                   compute_all=options['compute_all'])
    #
    # elif options['command'] == 'maturation' or options['command'] == 'fma':
    #     tools.fetalMaturationAnalysis.fetal_maturation_analysis(inputdir, round_digits=round_digits,
    #                                                             sep2read=read_sep, sep2write=write_sep,
    #                                                             line_term=line_term,
    #                                                             specific_storage=options["output_path"],
    #                                                             num_of_columns_to_keep=options["cols_2_keep"],
    #                                                             encoding=options["encoding"],
    #                                                             debug_flag=options["debug_mode"],
    #                                                             number_of_groups=options['number_of_groups'],
    #                                                             group_by=options['group_by'])
    #
    # elif options['command'] == 'clean_duration':
    #     tools.durationFromSingleDS.compute_duration_from_dirs(inputdir)
