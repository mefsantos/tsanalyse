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
import logging
import argparse
import tools.entropy
import tools.compress
import tools.stv_analysis as stv
import tools.utilityFunctions as util


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

    compress = subparsers.add_parser('compress', help='Compress all the files in the given directory')
    tools.compress.add_parser_options(compress)
    tools.utilityFunctions.add_csv_parser_options(compress)
    tools.utilityFunctions.add_numbers_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='Calculate entropy for all the files in the given directory')
    tools.entropy.add_parser_options(entropy)
    # TODO: need to add csv parser options to entropy module

    stv = subparsers.add_parser('stv', help='Perform Short-term Variability analysis with the following algorithms: '
                                            '%s' % stv.AVAILABLE_ALGORITHMS)
    tools.stv_analysis.add_parser_options(stv)
    tools.utilityFunctions.add_csv_parser_options(stv)

    args = parser.parse_args()
    options = vars(args)
    # parser definition ends

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

    if not os.path.isdir(inputdir):
        output_name = os.path.join(util.RUN_ISOLATED_FILES_PATH, os.path.basename(util.remove_file_extension(inputdir)))
    else:
        output_name = inputdir

    if options['command'] == 'compress':
        compressor = options['compressor']
        level = tools.compress.set_level(options)
        resulting_dict = tools.compress.compress(inputdir, compressor, level, False,
                                                 options['comp_ratio'], round_digits)

        outfile = "%s_%s_lvl_%d" % (output_name, compressor, level)
        if options['comp_ratio']:
            outfile += "_wCR"
        outfile += ".csv"

        output_file = open(outfile, "w")
        writer = csv.writer(output_file, delimiter=options["write_separator"], lineterminator=options["line_terminator"])
        header = ["Filename", "Original_Size", "Compressed_Size"]
        if options['comp_ratio']:
            header.append("CRx100")

        writer.writerow(header)

        for filename in sorted(resulting_dict.keys()):
            cd = resulting_dict[filename]
            data_row = [filename, cd.original, cd.compressed]
            if options['comp_ratio']:
                data_row.append(cd.compression_rate)

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
