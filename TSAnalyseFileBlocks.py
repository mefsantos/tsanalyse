#!/usr/bin/python
# -*- coding: utf-8 -*-
"""

Copyright (C) 2012 Mara Matias

This file is part of HRFAnalyse.

    HRFAnalyse is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published
    by the Free Software Foundation, either version 3 of the License,
    or (at your option) any later version.

    HRFAnalyse is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with HRFAnalyse.  If not, see
    <http://www.gnu.org/licenses/>.

_______________________________________________________________________________

HRFAnalyseFileBlocks is an auxiliary command line interface to apply one of the most common operations
we used.

This interface takes a file or directory, breaks each file into blocks and compresses each of the
generated blocks directories.


Usage: ./HRFAnalyseFileBlocks.py [BLOCK OPTIONS] INPUTFILE COMMAND [COMMAND OPTIONS]

To define how to create the blocks you can change BLOCK OPTIONS:

  --start-at-end        Partition from end of file instead of beginning
  -ds SECONDS, --defered-start SECONDS
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


entropy: This command allows you to calculate the entropy for all
     files in a given directory.
    
     OUTCOME: Calling this commmand will create a csv file using ';'
     as a field delimiter. The entropy measure and the
     optons used are appended to name the resulting file. This
     file will be created in the parent of the directory we are
     working with. Each file is represented by a row with two columns,
     the number of the block and it's entropy.


    COMMAND_OPTIONS are the available entropy measures:

     sampen              Sample Entropy
     apen                Aproximate Entropy
     apenv2              A slightly different implementation of Aproximate Entropy

    For a particular function's documentation please look at:
             pyeeg (http://code.google.com/p/pyeeg/downloads/list)

Examples:


=>Compress

Cut files into 5min blocks with no overlap and compress each one with the default compressor

./HRFAnalyseFileBlocks.py unittest_dataset/ -s 300 compress


Cut files into blocks with 300 lines with no overlap and compress each one with the default compressor

./HRFAnalyseFileBlocks.py unittest_dataset/ -s 300 --use-lines compress


Cut files into blocks with 5 min where one block starts 1 min later then the previous one did.
Compress each one with the paq8l compressor

./HRFAnalyseFileBlocks.py unittest_dataset/ -s 300 -g 60 compress -c paq8l


=>Entropy

Cut files into blocks with 5 min where one block starts 1 min later then the previous one did.
Calculate each files entropy using the Sample entropy.

./HRFAnalyseFileBlocks.py unittest_dataset/ -s 300 -g 60 entropy sampen


"""

import argparse
import tools.partition
import tools.compress
import tools.entropy
import tools.separate_blocks
import os
import csv
import logging

# TODO: add another parameter (sampling_frequency) in order to partition by seconds

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analysis of the file's blocks")
    parser.add_argument("inputfile", metavar="INPUT FILE", help="File to be analysed")
    parser.add_argument("--log", action="store", metavar="LOGFILE", default=None, dest="log_file",
                        help="Use LOGFILE to save logs.")
    parser.add_argument("--log-level", dest="log_level", action="store", help="Set Log Level; default:[%(default)s]",
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"], default="WARNING")

    tools.partition.add_parser_options(parser, full_file_option=False)

    subparsers = parser.add_subparsers(help='Different commands to be run on directory', dest="command")

    compress = subparsers.add_parser('compress', help='compress all the files in the given directory')
    tools.compress.add_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='calculate entropy for all the files in the given directory')
    tools.entropy.add_parser_options(entropy)
    #    tools.separate_blocks.add_parser_options(parser)

    args = parser.parse_args()
    options = vars(args)

    logger = logging.getLogger('hrfanalyse')
    logger.setLevel(getattr(logging, options['log_level']))

    if options['log_file'] is None:
        log_output = logging.StreamHandler()
    else:
        log_output = logging.FileHandler(options['log_file'])
    log_output.setLevel(getattr(logging, options['log_level']))
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    log_output.setFormatter(formatter)
    logger.addHandler(log_output)

    if options['inputfile'].endswith('/'):
        options['inputfile'] = options['inputfile'][:-1]

    if os.path.isdir(options['inputfile']):
        dest_dir = "%s_parts_%d_%d" % (options['inputfile'], options['section'], options['gap'])
    else:
        dest_dir = "%s_parts_%d_%d" % (os.path.dirname(options['inputfile']), options['section'], options['gap'])
    if not os.path.isdir(dest_dir):
        logger.info("Creating %s!" % dest_dir)
        os.makedirs(dest_dir)

    logger.info("%s will be used to store file partitions" % dest_dir)

    block_minutes = {}
    logger.info("Partitioning file in %d minutes intervals with %d gaps " % (options['section'], options['gap']))
    if options['gap'] == 0:
        options['gap'] = options['section']
    block_minutes = tools.partition.partition(options['inputfile'],
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
                                                        options['compressor'], options['level'], options['decompress'])
            logger.info("Compression complete")
        for filename in compressed:
            if options['decompress']:
                fboutname = "%s_decompress_%s.csv" % (filename, options['compressor'])
            else:
                fboutname = "%s_%s_lvl_%s.csv" % (filename, options['compressor'], options['level'])
            writer = csv.writer(open(fboutname, "w"), delimiter=";")
            header = ["Block", "Original Size", "Compressed Size"]
            if options['decompress']:
                header.append("Decompression Time")
            writer.writerow(header)
            for blocknum in range(1, len(compressed[filename]) + 1):
                block_results = compressed[filename]['%s_%d' % (filename, blocknum)]
                row_data = [blocknum, block_results.original, block_results.compressed]
                if options['decompress']:
                    row_data.append(block_results.time)
                writer.writerow(row_data)

            print("Storing into: %s" % os.path.abspath(fboutname))

    elif options['command'] == 'entropy':
        entropy = {}
        for filename in block_minutes:
            bfile = os.path.splitext(filename)[0]
            logger.info("Entropy calculations started for %s" % os.path.join(dest_dir, "%s_blocks" % bfile))
            files_stds = tools.entropy.calculate_std(os.path.join(dest_dir, "%s_blocks" % bfile))
            tolerances = dict((filename, files_stds[filename] * options["tolerance"]) for filename in files_stds)
            entropy[bfile] = tools.entropy.entropy(os.path.join(dest_dir, "%s_blocks" % bfile),
                                                   options['entropy'],
                                                   options['dimension'],
                                                   tolerances)
            logger.info("Entropy calculations complete")
        for filename in entropy:
            fboutname = "%s_%s_dim_%d_tol_%.2f.csv" % (filename, options['entropy'], options['dimension'], options['tolerance'])
            writer = csv.writer(open(fboutname, "w"), delimiter=";")
            header = ["Block", "Entropy"]
            writer.writerow(header)
            for blocknum in range(1, len(entropy[filename]) + 1):
                block_results = entropy[filename]['%s_%d' % (filename, blocknum)]
                row_data = [blocknum, block_results.entropy]
                writer.writerow(row_data)

            print("Storing into: %s" % os.path.abspath(fboutname))
