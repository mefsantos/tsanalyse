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

TSAnalyseFileBlocks is an auxiliary command line interface to apply one of the most common operations
we used.

This interface takes a file or directory, breaks each file into blocks and compresses each of the
generated blocks directories.


Usage: ./TSAnalyseFileBlocks.py [BLOCK OPTIONS] INPUTFILE COMMAND [COMMAND OPTIONS]

To define how to create the blocks you can change BLOCK OPTIONS:

  -ds SECONDS, --deferred-start SECONDS
                        Time gap between the start of the file and the start
                        of the interval; default:[0]
  -s SECONDS, --section SECONDS
                        Amount of time in seconds to be captured
  -g SECONDS, --gap SECONDS
                        gap between sections (if using --full-file option)
  --use-lines           Partition using line count instead of time

There are two command available compress and entropy.

compress: This command allows you to compress all the files in the
     given directory.  The list of available compressors is
     dynamically generated based on their availability in the system,
     below is the full list of all implemented compression algorithms.
     Unless changed the compression level used is always the max for
     the chosen algorithm (refer to the compressor's manual for this
     information).


     OUTCOME: Calling this command will create a csv file using ';'
     as a field delimiter for each file in the _blocks directory.
     The compression algorithm and the compression level used are used
     to name the resulting file. This file will be created in the
     parent of the directory we are
     working with. Each file is represented by a row with three
     columns, the number of the block, it's original size and it's
     compressed size.

     COMMAND_OPTIONS for this command are:
     -c COMPRESSOR, --compressor COMPRESSOR
                        compression compressor to be used, available
                        compressors:paq8l, lzma, gzip, zip, bzip2, ppmd,
                        zlib, spbio;default:[first on the list - lmza]
     --level LEVEL      compression level to be used, this variable is
                        compressor dependent; default:[The maximum of whatever
                        compressor was chosen]
     --decompression    Use this option if you also wish to calculate how long it takes to
                        decompress the file once it's compressed
     -cr, --with-compression-ratio      Add an additional column with the compression ratio


entropy: This command allows you to calculate the entropy for all
     files in a given directory.

     OUTCOME: Calling this command will create a csv file using ';'
     as a field delimiter. The entropy measure and the
     options used are appended to name the resulting file. This
     file will be created in the parent of the directory we are
     working with. Each file is represented by a row with two columns,
     the number of the block and it's entropy.


    COMMAND_OPTIONS are the available entropy measures:

     sampen              Sample Entropy
     apen                Approximate Entropy
     apenv2              A slightly different implementation of Aproximate Entropy

    For a particular function's documentation please look at:
             pyeeg (http://code.google.com/p/pyeeg/downloads/list)

Examples:


=>Compress

Cut files into 5min blocks with no overlap and compress each one with the default compressor

./TSAnalyseFileBlocks.py unittest_dataset/ -s 300 compress


Cut files into blocks with 300 lines with no overlap and compress each one with the default compressor

./TSAnalyseFileBlocks.py unittest_dataset/ -s 300 --use-lines compress


Cut files into blocks with 5 min where one block starts 1 min later then the previous one did.
Compress each one with the paq8l compressor

./TSAnalyseFileBlocks.py unittest_dataset/ -s 300 -g 60 compress -c paq8l


=>Entropy

Cut files into blocks with 5 min where one block starts 1 min later then the previous one did.
Calculate each files entropy using the Sample entropy.

./TSAnalyseFileBlocks.py unittest_dataset/ -s 300 -g 60 entropy sampen


"""

import os
import csv
import logging
import argparse
import tools.entropy
import tools.compress
import tools.partition
import tools.separate_blocks
import tools.utilityFunctions as util

# TODO: add another parameter (sampling_frequency) in order to partition by seconds

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Analysis of the file's blocks")
    parser.add_argument("inputfile", metavar="INPUT FILE", help="File to be analysed")
    parser.add_argument("--log", action="store", metavar="LOGFILE", default=None, dest="log_file",
                        help="Use LOGFILE to save logs.")
    parser.add_argument("--log-level", dest="log_level", action="store", help="Set Log Level; default:[%(default)s]",
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"], default="WARNING")

    tools.partition.add_parser_options(parser, full_file_option=False, file_blocks_usage=True)

    subparsers = parser.add_subparsers(help='Different commands to be run on directory', dest="command")

    compress = subparsers.add_parser('compress', help='compress all the files in the given directory')
    tools.compress.add_parser_options(compress)
    tools.utilityFunctions.add_csv_parser_options(compress)
    tools.utilityFunctions.add_numbers_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='calculate entropy for all the files in the given directory')
    tools.entropy.add_parser_options(entropy)
    #    tools.separate_blocks.add_parser_options(parser)

    args = parser.parse_args()
    options = vars(args)

    logger = logging.getLogger('tsanalyse')
    logger.setLevel(getattr(logging, options['log_level']))

    # THESE OPTIONS ARE DISABLED FOR NOW
    options['start_at_end'] = False
    options['decompress'] = None

    # TODO: later we might remove this when every command accepts these flags
    read_sep = options['read_separator'] if hasattr(args, "read_separator") else ";"
    write_sep = options['write_separator'] if hasattr(args, "write_separator") else ";"
    line_term = options['line_terminator'] if hasattr(args, "line_terminator") else "\n"

    round_digits = options['round_digits'] if hasattr(args, "round_digits") else None
    round_digits = int(round_digits) if round_digits is not None else None

    if options['log_file'] is None:
        log_output = logging.StreamHandler()
    else:
        log_output = logging.FileHandler(options['log_file'])
    log_output.setLevel(getattr(logging, options['log_level']))
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    log_output.setFormatter(formatter)
    logger.addHandler(log_output)

    inputdir = options['inputfile'].strip()
    inputdir = util.remove_slash_from_path(inputdir)  # if slash exists

    if not os.path.exists(util.BLOCK_ANALYSIS_OUTPUT_PATH):
        logger.info("Creating %s..." % util.BLOCK_ANALYSIS_OUTPUT_PATH)
        os.mkdir(util.BLOCK_ANALYSIS_OUTPUT_PATH)

    if not os.path.exists(util.FILE_BLOCKS_STORAGE_PATH):
        logger.info("Creating %s..." % util.BLOCK_ANALYSIS_OUTPUT_PATH)
        os.mkdir(util.FILE_BLOCKS_STORAGE_PATH)

    file_blocks_suffix = "sec_%d_gap_%d" % (options['section'], options['gap'])
    dataset_suffix_name = "%s_parts_%s" % (util.get_dataset_name_from_path(inputdir), file_blocks_suffix)

    dest_dir = os.path.join(util.FILE_BLOCKS_STORAGE_PATH, dataset_suffix_name)

    if not os.path.exists(dest_dir):
        logger.info("Creating %s..." % dest_dir)
        os.mkdir(dest_dir)

    logger.info("%s will be used to store file partitions" % dest_dir)

    block_minutes = {}
    logger.info("Partitioning file in %d minutes intervals with %d gaps " % (options['section'], options['gap']))
    if options['gap'] == 0:
        options['gap'] = options['section']
    block_minutes = tools.partition.partition(inputdir,
                                              dest_dir,
                                              options['partition_start'],
                                              options['section'],
                                              options['gap'],
                                              options['start_at_end'],
                                              True,
                                              options['using_lines'])
    logger.info("Partitioning complete")

    if options['command'] == 'compress':
        compressed = {}
        options['level'] = tools.compress.set_level(options)
        for filename in block_minutes:
            bfile = os.path.splitext(filename)[0]
            logger.info("Compression started for %s" % os.path.join(dest_dir, "%s_blocks" % filename))
            # The extensions had to be removed from the original name when
            # creating the block for compatibility with windows, so this line
            # changes the filename
            compressed[bfile] = tools.compress.compress(os.path.join(dest_dir, "%s_blocks" % bfile),
                                                        options['compressor'], options['level'],
                                                        options['decompress'], options['comp_ratio'], round_digits)
            logger.info("Compression complete")

        for filename in compressed:
            if options['decompress']:
                fboutsuffix = "%s_%s_decompress_%s" % (os.path.basename(filename),
                                                       file_blocks_suffix,
                                                       options['compressor'])
            else:
                fboutsuffix = "%s_%s_%s_lvl_%s" % (os.path.basename(filename),
                                                   file_blocks_suffix,
                                                   options['compressor'],
                                                   options['level'])
            if options['comp_ratio']:
                fboutsuffix += "_wCR"

            fboutsuffix += ".csv"

            fboutname = os.path.join(util.BLOCK_ANALYSIS_OUTPUT_PATH, fboutsuffix)

            file_to_write = open(fboutname, "w")
            writer = csv.writer(file_to_write, delimiter=";")
            header = ["Block", "Original Size", "Compressed Size"]
            if options['comp_ratio']:
                header.append("CRx100")
            if options['decompress']:
                header.append("Decompression Time")
            writer.writerow(header)

            for blocknum in range(1, len(compressed[filename]) + 1):
                block_results = compressed[filename]['%s_%d' % (filename, blocknum)]
                row_data = [blocknum, block_results.original, block_results.compressed]
                if options['comp_ratio']:
                    row_data.append(block_results.compression_rate)
                if options['decompress']:
                    row_data.append(block_results.time)
                writer.writerow(row_data)

            print("Storing into: %s" % os.path.abspath(fboutname))
            file_to_write.close()

    elif options['command'] == 'entropy':
        entropy = {}
        for filename in block_minutes:
            bfile = os.path.splitext(filename)[0]
            logger.info("Entropy calculations started for %s" % os.path.join(dest_dir, "%s_blocks" % bfile))
            files_stds = tools.entropy.calculate_std(os.path.join(dest_dir, "%s_blocks" % bfile))
            tolerances = dict((filename, files_stds[filename] * options["tolerance"]) for filename in files_stds)
            entropy[bfile] = tools.entropy.entropy(os.path.join(dest_dir, "%s_blocks" % bfile), options['entropy'],
                                                   options['dimension'], tolerances, round_digits)
            logger.info("Entropy calculations complete")

        for filename in entropy:
            fboutsuffix = "%s_%s_%s_dim_%d_tol_%.2f.csv" % (os.path.basename(filename), file_blocks_suffix,
                                                            options['entropy'], options['dimension'],
                                                            options['tolerance'])

            fboutname = os.path.join(util.BLOCK_ANALYSIS_OUTPUT_PATH, fboutsuffix)

            file_to_write = open(fboutname, "w")
            writer = csv.writer(file_to_write, delimiter=";")
            header = ["Block", "Entropy"]
            writer.writerow(header)
            for blocknum in range(1, len(entropy[filename]) + 1):
                block_results = entropy[filename]['%s_%d' % (filename, blocknum)]
                row_data = [blocknum, block_results.entropy]
                writer.writerow(row_data)

            print("Storing into: %s" % os.path.abspath(fboutname))
            file_to_write.close()
