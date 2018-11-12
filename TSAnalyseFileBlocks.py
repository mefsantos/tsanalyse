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
  -ul, --use-lines      Partition using line count instead of time
  -kb, --keep-blocks    After processing file blocks maintain the partitions
                        generated

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
     # disabled --decompression    Use this option if you also wish to calculate how long it takes to
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
import shutil
import logging
import argparse
import tools.entropy
import tools.compress
import tools.partition
import tools.separate_blocks
import tools.utilityFunctions as util

# TODO: add another parameter (sampling_frequency) in order to partition by seconds

if __name__ == "__main__":

    if not os.path.exists(util.RUN_ISOLATED_FILES_PATH):
        os.mkdir(util.RUN_ISOLATED_FILES_PATH)

    parser = argparse.ArgumentParser(description="Analysis of the file's blocks")
    parser.add_argument("input_path", metavar="INPUT PATH", action="store", nargs="+",
                        help="Path for a file or directory containing the datasets to be used as input")

    tools.utilityFunctions.add_logger_parser_options(parser)
    tools.partition.add_parser_options(parser, full_file_option=False, file_blocks_usage=True)
    #    tools.separate_blocks.add_parser_options(parser)
    tools.utilityFunctions.add_csv_parser_options(parser)

    subparsers = parser.add_subparsers(help='Different commands to be run on directory', dest="command")

    compress = subparsers.add_parser('compress', help='compress all the files in the given directory')
    tools.compress.add_parser_options(compress)
    tools.utilityFunctions.add_numbers_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='calculate entropy for all the files in the given directory')
    tools.entropy.add_parser_options(entropy)
    tools.utilityFunctions.add_numbers_parser_options(entropy)

    args = parser.parse_args()
    options = vars(args)

    logger = util.initialize_logger(logger_name="tsanalyse", log_file=options["log_file"],
                                    log_level=options["log_level"], with_first_entry="TSAnalyseFileBlocks")

    # THESE OPTIONS ARE DISABLED FOR NOW
    options['start_at_end'] = False
    options['decompress'] = None

    change_output_location = False
    specified_output = os.path.expanduser(options["output_path"]) if options["output_path"] is not None else None
    specified_output = util.remove_slash_from_path(specified_output)  # if slash exists

    block_analysis_storage = util.BLOCK_ANALYSIS_OUTPUT_PATH

    if specified_output is not None:
        if os.path.exists(specified_output):
            logger.info("Using specified output destination.")
            specified_output = os.path.abspath(specified_output)
            block_analysis_storage = os.path.join(specified_output, "block_analysis")
            change_output_location = True
        else:
            logger.warning("Specified folder '%s' does not exist. Ignoring..." % specified_output)

    if not os.path.exists(util.FILE_BLOCKS_STORAGE_PATH):
        logger.warning("Output directory for file blocks does not exist.")
        logger.info("Creating '%s'..." % util.FILE_BLOCKS_STORAGE_PATH)
        os.mkdir(util.FILE_BLOCKS_STORAGE_PATH)

    iterable_input_path = options['input_path'][0].split(" ") if len(options['input_path']) == 1 else options['input_path']

    for inputs in iterable_input_path:
        inputdir = inputs.strip()
        inputdir = util.remove_slash_from_path(inputdir)
        inputdir = os.path.expanduser(inputdir)  # to handle the case of paths as a string

        if not os.path.isdir(inputdir):
            output_location = os.path.join(block_analysis_storage, "individual_runs")
        else:
            output_location = os.path.join(block_analysis_storage, os.path.basename(inputdir))

        if not os.path.exists(output_location):
            if not change_output_location:  # we just want to display this message if we use the default path
                logger.warning("Output directory for block analysis does not exist.")
            logger.info("Creating '%s'..." % output_location)
            os.makedirs(output_location)

        file_blocks_suffix = "sec_%d_gap_%d" % (options['section'], options['gap'])
        dataset_suffix_name = "%s_parts_%s" % (util.get_dataset_name_from_path(inputdir), file_blocks_suffix)

        blocks_dir = os.path.join(util.FILE_BLOCKS_STORAGE_PATH, dataset_suffix_name)

        if not os.path.exists(blocks_dir):
            logger.info("Creating %s..." % blocks_dir)
            os.mkdir(blocks_dir)

        logger.info("Starting partition procedures")
        logger.info("File partitions will be stored in '%s'" % blocks_dir)

        block_minutes = {}
        logger.info("Partitioning file in %d minutes intervals with %d gaps " % (options['section'], options['gap']))
        if options['gap'] == 0:
            options['gap'] = options['section']
        try:
            block_minutes = tools.partition.partition(inputdir,
                                                      blocks_dir,
                                                      options['partition_start'],
                                                      options['section'],
                                                      options['gap'],
                                                      options['start_at_end'],
                                                      True,
                                                      options['using_lines'])
        except ValueError:
            logger.critical("The file '%s' does not contain the necessary columns for the evaluation. "
                            "Please make sure the file has two columns: "
                            "the first with the timestamps and the second with the hrf values." % inputdir)
            logger.info("Skipping ...")
            logger.info("Removing destination directories")
            try:
                os.removedirs(blocks_dir)
            except OSError as err:
                logger.warning("OS error: {0}".format(err))
                logger.warning("skipping directory removal...")
                pass
        else:
            logger.info("Partitioning complete")

            if options['command'] == 'compress':
                compressed = {}
                options['level'] = tools.compress.set_level(options)
                for filename in block_minutes:
                    bfile = os.path.splitext(filename)[0]
                    logger.info("Compression started for %s" % os.path.join(blocks_dir, "%s_blocks" % filename))
                    # The extensions had to be removed from the original name when the block for compatibility
                    # with windows, so this line changes the filename
                    compressed[bfile] = tools.compress.compress(os.path.join(blocks_dir, "%s_blocks" % bfile),
                                                                options['compressor'], options['level'],
                                                                options['decompress'], options['comp_ratio'],
                                                                options["round_digits"])
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

                    fboutname = os.path.join(output_location, fboutsuffix)

                    file_to_write = open(fboutname, "w")
                    writer = csv.writer(file_to_write, delimiter=options["write_separator"],
                                        lineterminator=options["line_terminator"])
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

                    file_to_write.close()
                    logger.info("Storing into: %s" % os.path.abspath(fboutname))

            elif options['command'] == 'entropy':
                algorithm = options['algorithm']
                entropy = {}
                for filename in block_minutes:
                    bfile = os.path.splitext(filename)[0]
                    logger.info("Entropy calculations started for %s" % os.path.join(blocks_dir, "%s_blocks" % bfile))
                    files_stds = tools.entropy.calculate_std(os.path.join(blocks_dir, "%s_blocks" % bfile))
                    tolerances = dict((filename, files_stds[filename] * options["tolerance"]) for filename in files_stds)
                    entropy[bfile] = tools.entropy.entropy(os.path.join(blocks_dir, "%s_blocks" % bfile), algorithm,
                                                           options['dimension'], tolerances, options["round_digits"])
                    logger.info("Entropy calculations complete")

                for filename in entropy:
                    fboutsuffix = "%s_%s_%s_dim_%d_tol_%.2f.csv" % (os.path.basename(filename), file_blocks_suffix,
                                                                    algorithm, options['dimension'],
                                                                    options['tolerance'])
                    fboutname = os.path.join(output_location, fboutsuffix)

                    file_to_write = open(fboutname, "w")
                    writer = csv.writer(file_to_write, delimiter=options["write_separator"], lineterminator=options["line_terminator"])

                    header = ["Block", "Entropy"]
                    writer.writerow(header)
                    for blocknum in range(1, len(entropy[filename]) + 1):
                        block_results = entropy[filename]['%s_%d' % (filename, blocknum)]
                        row_data = [blocknum, block_results.entropy]
                        writer.writerow(row_data)

                    file_to_write.close()
                    logger.info("Storing into: %s" % os.path.abspath(fboutname))

        if not options["keep_blocks"]:
            logger.info("Deleting scales directory: %s" % blocks_dir)
            shutil.rmtree(blocks_dir, ignore_errors=True)

    logger.info("Done")
