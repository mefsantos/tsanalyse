"""
Copyright (C) 2012 Mara Matias

Edited by Duarte Ferreira - 2016
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

COMPRESSORS IMPLEMENTED: paq8l, lzma, gzip, bzip2, ppmd, spbio.

!!!IMPLEMENTATION NOTE: Not all the compressor have an 'outpufile' parameter, which
means those compressors produce a compressed file with the exact same name as the
original but with some extra prefix. To maintain some coherence throughout the code
a choice was made to force the same behavior in all the compressors who write 
output files. This however means the same directory/file cannot be compressed in
the same machine at the same time since one of the processes could delete or rewrite
the temporary file before the other was finished using it!!!

MODULE EXTERNAL DEPENDENCIES: 
                     lzma module for python.
                     ppmd and paq8l - sources included in the package, and spbio(Windows only) have to be installed in
                      the system path if you would like to use them. - performed automatically in Linux


ENTRY POINT: compress(input_name, compression_algorithm, level, decompress, with_compression_rate, digits_to_round)

"""

# TODO: later i might want to use subprocess import to run C commands instead so i can capture the output + errors
import os
import sys
import bz2
import zlib
import time
import brotli
import timeit
import logging
import subprocess
from collections import namedtuple
from shutil import rmtree

try:
    import utility_functions as util
except ImportError:
    import tools.utility_functions as util

try:
    import lzma

    lzma_available = True
except ImportError:
    try:
        import pylzma as lzma

        lzma_available = True
    except ImportError:
        lzma_available = False

module_logger = logging.getLogger('tsanalyse.compress')

# DATA TYPE DEFINITIONS
"""
This is a data type defined to be used as a return for compression it has four attributes:
    - original: contains the original size of the file
    - compressed: the size of the resulting compressed file
    - compression_rate: the compression rate of the file (None if its not computed)
    - time: the time it takes to decompress (None if the timing is not run)
"""
CompressionData = namedtuple('CompressionData', 'original compressed compression_rate time')


# Setup the environment with paths for the third-party compressors
util.setup_environment()


# ENTRY POINT FUNCTION
def compress(input_name, compression_algorithm, level, decompress=False,
             with_compression_rate=False, digits_to_round=None):
    """
    Given a file or directory named input_name, apply the desired
    compression algorithm to all the files. Optionally a timing on
    decompression may also be run.

    Levels will be set to the compressor's maximum or minimum respectively
    if the level passed as argument is not valid.

    :param input_name: string containing the name of the dataset to read
    :param compression_algorithm: string containing the name of the compressor to use
    :param level: integer containing the level of compression to use
    :param decompress: boolean flag to determine whether to output the decompression time or not
    :param with_compression_rate: boolean flag to determine whether to compute the compression rate or not
    :param digits_to_round: integer containing the number of digits to use when rounding floats/doubles
    :return dictionary of 'string : CompressionData' with:
        the original size, compressed size, compression rate*, decompression time*

    * optional
    """
    level = abs(level)
    digits_to_round = None if not digits_to_round else abs(digits_to_round)

    compressed = {}
    method_to_call = getattr(sys.modules[__name__], compression_algorithm.lower() + '_compress')

    if level > AVAILABLE_COMPRESSORS[compression_algorithm][1]:
        level = AVAILABLE_COMPRESSORS[compression_algorithm][1]
    elif level < AVAILABLE_COMPRESSORS[compression_algorithm][0]:
        level = AVAILABLE_COMPRESSORS[compression_algorithm][0]

    if os.path.isdir(input_name):
        module_logger.info("Using %s to compress files in directory '%s'"
                           % (compression_algorithm, util.remove_project_path_from_file(input_name)))
        filelist = util.listdir_no_hidden(input_name)
        for filename in filelist:
            filename = filename.strip()  # removes the trailing \n
            compression_data = method_to_call(os.path.join(input_name, filename), level,
                                              decompress, with_compression_rate, digits_to_round)
            compressed[filename] = compression_data
    else:
        module_logger.info("Using %s to compress file '%s'"
                           % (compression_algorithm, util.remove_project_path_from_file(input_name)))
        entry_name = os.path.basename(input_name.strip())
        compression_data = method_to_call(input_name.strip(), level, decompress, with_compression_rate, digits_to_round)
        compressed[entry_name] = compression_data

    # we will move this log to the interfaces to avoid "spam" when debugging multiscale
    # module_logger.debug("Compression data: {0}".format(compressed))
    return compressed


# IMPLEMENTATION
def gzip_compress(inputfile, level, decompress, compute_compression_rate=None, digits_to_round=None):
    """
    Compresses one file using the python implementation of zlib.

    NOTE: Although this uses the name gzip the actual tool being used
    is python's zlib which has the actual implementation of the deflate
    compression algorithm. This is possible because the only difference between
    gzip and zlib is the header added to the compressed file, which is not in the
    resulting compressed string, nor is it added in our case.

    :param input_file: string containing the name of the file to read
    :param level: integer containing the level of compression to use
    :param decompress: boolean flag to obtain the decompression time
    :param compute_compression_rate: boolean flag to enable computing the compression rate
    :param digits_to_round: integer containing the number of digits to use when rounding floats/doubles
    :return  CompressionData
    """

    original_size = int(os.stat(inputfile).st_size)
    with open(inputfile, "rU") as fdorig:
        origlines = fdorig.read()
    origtext = memoryview(bytearray(origlines, "utf8"))
    compressedtext = memoryview(zlib.compress(origtext.tobytes(), int(level)))
    compressed_size = len(compressedtext)
    compression_rate = None
    decompress_time = None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: zlib.decompress(compressedtext.tobytes()),
                                            number=10,
                                            repeat=3, timer=time.clock))
    if compute_compression_rate:
        compression_rate = util.compression_rate(original_size, compressed_size, digits_to_round, module_logger)

    cd = CompressionData(original_size, compressed_size, compression_rate, decompress_time)
    return cd


def paq8l_compress(input_file, level, decompress, compute_compression_rate=None, digits_to_round=None):
    """
    Compresses one file using the paq8l compressor.
    The size is determined by querying the file paq8l creates, this temporary file
    is removed at the end of this function.

    :param input_file: string containing the name of the file to read
    :param level: integer containing the level of compression to use
    :param decompress: boolean flag to obtain the decompression time
    :param compute_compression_rate: boolean flag to enable computing the compression rate
    :param digits_to_round: integer containing the number of digits to use when rounding floats/doubles
    :return  CompressionData
    """
    subprocess.check_output('paq8l -%d "%s"' % (level, input_file), shell=True, stderr=subprocess.STDOUT)
    original_size = int(os.stat(input_file).st_size)
    compressed_size = int(os.stat(input_file + '.paq8l').st_size)
    compression_rate = None
    decompress_time = None
    #
    # if decompress:
    #     decompress_time = min(timeit.repeat(
    #         'subprocess.check_output(\'paq8l -d "%s.paq8l"\',shell=True,stderr=subprocess.STDOUT)' % input_file,
    #         number=1,
    #         repeat=3,
    #         setup='import subprocess'))

    if decompress:
        decompress_time = min(
            timeit.repeat(
                'subprocess.check_output({0},'
                ' shell=True,'
                ' stderr=subprocess.STDOUT)'.format('paq8l -%d "%s"' % (level, input_file)),
                number=1,
                repeat=3,
                setup='import subprocess'
            )
        )

    rmtree('%s.paq8l' % input_file, ignore_errors=True)

    if compute_compression_rate:
        compression_rate = util.compression_rate(original_size, compressed_size, digits_to_round, module_logger)

    cd = CompressionData(original_size, compressed_size, compression_rate, decompress_time)
    return cd


def lzma_compress(input_file, level, decompress, compute_compression_rate=None, digits_to_round=None):
    """
    Compresses one file using the python implementation of lzma.

    NOTE: The lzma module was created for python3, the backported version for
    python2.7, does not have a level parameter, a decision was made to keep this
    code backwards compatible so the level parameter is never used. The
    default the level being used is 6.

    :param input_file: string containing the name of the file to read
    :param level: integer containing the level of compression to use
    :param decompress: boolean flag to obtain the decompression time
    :param compute_compression_rate: boolean flag to enable computing the compression rate
    :param digits_to_round: integer containing the number of digits to use when rounding floats/doubles
    :return  CompressionData
     """

    original_size = int(os.stat(input_file).st_size)
    with open(input_file, "rU") as fdorig:
        origlines = fdorig.read()
    origtext = memoryview(bytearray(origlines, "utf8"))
    compressedtext = memoryview(lzma.compress(origtext.tobytes()))
    compressed_size = len(compressedtext)
    compression_rate = None
    decompress_time = None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: lzma.decompress(compressedtext.tobytes()),
                                            number=10,
                                            repeat=3, timer=time.clock))
    if compute_compression_rate:
        compression_rate = util.compression_rate(original_size, compressed_size, digits_to_round, module_logger)

    cd = CompressionData(original_size, compressed_size, compression_rate, decompress_time)
    return cd


def bzip2_compress(input_file, level, decompress, compute_compression_rate=None, digits_to_round=None):
    """
    Compresses one file using the python implementation of bzip2.

    :param input_file: string containing the name of the file to read
    :param level: integer containing the level of compression to use
    :param decompress: boolean flag to obtain the decompression time
    :param compute_compression_rate: boolean flag to enable computing the compression rate
    :param digits_to_round: integer containing the number of digits to use when rounding floats/doubles
    :return  CompressionData
    """

    original_size = int(os.stat(input_file).st_size)
    with open(input_file, "rU") as fdorig:
        origlines = fdorig.read()
    origtext = memoryview(bytearray(origlines, "utf8"))
    compressedtext = memoryview(bz2.compress(origtext.tobytes(), level))
    compressed_size = len(compressedtext)
    compression_rate = None
    decompress_time = None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: bz2.decompress(compressedtext.tobytes()),
                                            number=10,
                                            repeat=3, timer=time.clock))

    if compute_compression_rate:
        compression_rate = util.compression_rate(original_size, compressed_size, digits_to_round, module_logger)

    cd = CompressionData(original_size, compressed_size, compression_rate, decompress_time)
    return cd


def ppmd_compress(input_file, level, decompress, compute_compression_rate=None, digits_to_round=None):
    """
    Compresses one file using the ppmd compressor.

    NOTE: This algorithm does not have a standard level, but the model
    order behaves as a compression level, so level here refers to the
    order level. Maximum memory is always used.

    :param input_file: string containing the name of the file to read
    :param level: integer containing the level of compression to use
    :param decompress: boolean flag to obtain the decompression time
    :param compute_compression_rate: boolean flag to enable computing the compression rate
    :param digits_to_round: integer containing the number of digits to use when rounding floats/doubles
    :return  CompressionData
    """

    subprocess.check_output('ppmd e -s -f"{0}.ppmd" -m256 -o{1} "{0}"'.format(input_file, level), shell=True,
                            stderr=subprocess.STDOUT)

    original_size = int(os.stat(input_file).st_size)
    compressed_size = int(os.stat(input_file + '.ppmd').st_size)
    compression_rate = None
    decompress_time = None
    if decompress:
        decompress_time = min(
            # timeit.repeat(
            #     'subprocess.call(\'ppmd d -s "%s.ppmd"\',shell=True,stderr=subprocess.STDOUT)' % input_file,
            #     number=5,
            #     repeat=3,
            #     setup='import subprocess'))

            timeit.repeat(
                'subprocess.check_output({0},'
                ' shell=True,'
                ' stderr=subprocess.STDOUT)'.format('ppmd e -s -f"{0}.ppmd" -m256 -o{1} "{0}"'.format(input_file, level)),
                number=5,
                repeat=3,
                setup='import subprocess'
            )
        )

    rmtree('%s.ppmd' % input_file, ignore_errors=True)

    if compute_compression_rate:
        compression_rate = util.compression_rate(original_size, compressed_size, digits_to_round, module_logger)

    cd = CompressionData(original_size, compressed_size, compression_rate, decompress_time)
    return cd


def spbio_compress(input_file, level, decompress, compute_compression_rate=None, digits_to_round=None):
    """
    Compresses one file using the spbio tool.

    NOTE: This compressor is only available for Windows and has no
    compression levels.

    :param input_file: string containing the name of the file to read
    :param level: integer containing the level of compression to use
    :param decompress: boolean flag to obtain the decompression time
    :param compute_compression_rate: boolean flag to enable computing the compression rate
    :param digits_to_round: integer containing the number of digits to use when rounding floats/doubles
    :return  CompressionData
    """

    os.system('spbio "' + input_file + '"')
    original_size = int(os.stat(input_file).st_size)
    compressed_size = int(os.stat(input_file + '.sph').st_size)
    os.remove(input_file + '.sph')

    compression_rate = None
    decompress_time = None
    if compute_compression_rate:
        compression_rate = util.compression_ratio(original_size, compressed_size, digits_to_round)

    cd = CompressionData(original_size, compressed_size, compression_rate, decompress_time)

    return cd


def brotli_compress(input_file, level, decompress, compute_compression_rate=None, digits_to_round=None):
    """
    Compresses one file using the brotli algorithm by google.

    :param input_file: string containing the name of the file to read
    :param level: integer containing the level of compression to use
    :param decompress: boolean flag to obtain the decompression time
    :param compute_compression_rate: boolean flag to enable computing the compression rate
    :param digits_to_round: integer containing the number of digits to use when rounding floats/doubles
    :return  CompressionData
    """

    original_size = int(os.stat(input_file).st_size)
    with open(input_file, "rU") as fdorig:
        origlines = fdorig.read()
    origtext = memoryview(bytearray(origlines, "utf8"))
    compressedtext = memoryview(brotli.compress(origtext.tobytes(), quality=int(level)))
    compressed_size = len(compressedtext)
    compression_rate = None
    decompress_time = None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: zlib.decompress(compressedtext.tobytes()),
                                            number=10,
                                            repeat=3, timer=time.clock))

    if compute_compression_rate:
        compression_rate = util.compression_rate(original_size, compressed_size, digits_to_round, module_logger)

    cd = CompressionData(original_size, compressed_size, compression_rate, decompress_time)
    return cd


# AUXILIARY FUNCTIONS
def is_compression_table_empty(compression_table):
    return all(map(lambda x: len(compression_table[x]) < 1, compression_table))


def test_compressors():
    """
    (NoneType) -> NoneType
    
    !!!Auxiliary function!!! Function to test the system path for available
    compressors from within the ones that are implemented.

    Minimum and maximum levels are defined according to the compressor,
    if there are no levels implemented both minimum and maximum are
    -1.
    """
    module_logger.info("Checking for available compressors")
    compressor_list = {"paq8l": (1, 8), "ppmd": (2, 16), "spbio": (-1, -1)}
    available = dict()
    available["gzip"] = (1, 9)
    available["bzip2"] = (1, 9)
    available["brotli"] = (1, 11)
    if lzma_available:
        available["lzma"] = (6, 6)
    exec_path = os.environ.get("PATH")
    exec_path = exec_path.split(';')
    if len(exec_path) == 1:
        exec_path = exec_path[0].split(':')
    for compressor in compressor_list.keys():
        os_paths = [os.path.join(dirpath, compressor)
                    for dirpath in exec_path if os.path.isfile(os.path.join(dirpath, compressor))]
        # print("resulting paths: %s" % os_paths)
        module_logger.debug("resulting paths: %s" % os_paths)
        os_paths_execs = [os.path.join(dirpath, compressor+".exe")
                          for dirpath in exec_path if os.path.isfile(os.path.join(dirpath, compressor+".exe"))]
        # print("resulting paths for executables: %s" % os_paths_execs)
        module_logger.debug("resulting paths for executables: %s" % os_paths_execs)
        if len(os_paths) > 0 or len(os_paths_execs) > 0:
            available[compressor] = compressor_list[compressor]
            # old code
            # for dir_in_path in exec_path:
            #     print os.path.join(dir_in_path, compressor)
            #     if os.path.exists(os.path.join(dir_in_path, compressor)) or os.path.exists(
            #             os.path.join(dir_in_path, compressor + '.exe')):
            #         available[compressor] = compressor_list[compressor]
            #         print "PATH %s EXIST!!!" % os.path.join(dir_in_path, compressor)
    # print("Available compressors: %s" % available)
    module_logger.info("Available compressors: %s" % available.keys())
    return available


# A constant with the list of available compressors in the path
AVAILABLE_COMPRESSORS = test_compressors()


def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the parameters taken by the entry function 
    in this module

    """
    parser.add_argument("-c",
                        "--compressor",
                        dest="compressor",
                        metavar="COMPRESSOR",
                        action="store",
                        choices=AVAILABLE_COMPRESSORS,
                        default=list(AVAILABLE_COMPRESSORS.keys())[0],
                        help="compressor to be used. Available compressors:" + ', '.join(
                            AVAILABLE_COMPRESSORS) + "; default:[%(default)s]")
    parser.add_argument("-l",
                        "--level",
                        dest="level",
                        metavar="LEVEL",
                        action="store",
                        type=int,
                        help="compression level to be used, this variable is compressor dependent; "
                             "default:[The maximum of whatever compressor was chosen]")
    parser.add_argument("-cr",
                        "--with-compression-rate",
                        dest="comp_rate",
                        action="store_true",
                        default=False,
                        help="Use this options if you want add a column to the final data set containing "
                             "the compression rate[(compressed size / uncompressed size) * 100]")
    # 28/02/18 - removed flags to avoid excessive unexplained functionalities (paper review)
    # parser.add_argument("-dt",
    #                     "--decompress-time",
    #                     dest="decompress",
    #                     action="store_true",
    #                     default=False,
    #                     help="Use this options if you want the decompression time instead of the compression size")


def set_level(options):
    """
    (dict of str: object) -> int

    !!!Auxiliary function!!!
    Return a valid value for level in the options to be within the maximum or minimum 
    levels for the chosen compressor.

    :param options: a dictionary containing all the parser options
    :return the correct level to be used by the compressor
    """
    max_level = max(AVAILABLE_COMPRESSORS[options['compressor']])
    min_level = min(AVAILABLE_COMPRESSORS[options['compressor']])

    module_logger.debug("Input level: %s. Available levels: %s" %
                        (options["level"], AVAILABLE_COMPRESSORS[options['compressor']]))
    if not options["level"]:
        module_logger.warning("Compression level not set. Setting level to maximum: %s " % max_level)
        level = max_level
    else:
        if options['level'] > AVAILABLE_COMPRESSORS[options['compressor']][1]:
            module_logger.warning("Compressor level above maximum. Setting level to maximum: %s" % max_level)
            level = max_level
        elif options['level'] < AVAILABLE_COMPRESSORS[options['compressor']][0]:
            module_logger.warning("Compressor level below minimum, setting level to minimum: %s" % min_level)
            level = min_level
        else:
            level = options['level']
            module_logger.info("Setting compression level of '%s' to '%s'" % (options["compressor"], options["level"]))
    return level
