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

This module implements the calculation of entropy (sample and approximate since
after some testing these seem to be the only ones that have significant results 
for our specific purposes. Some of the functions are calls to the pyeeg 
implementation.


MODULE EXTERNAL DEPENDENCIES:
pyeeg(http://code.google.com/p/pyeeg/downloads/list),
numpy(http://numpy.scipy.org/),

ENTRY POINT: entropy(input_name,function,dimension,tolerances)
             calculate_std(input_name)
"""

import os
import sys
import numpy
import logging
from collections import namedtuple

try:
    from tools.pyeeg import samp_entropy, ap_entropy
except ImportError:
    from pyeeg import samp_entropy, ap_entropy

try:
    import utility_functions as util
except Exception:
    import tools.utility_functions as util

AVAILABLE_ALGORITHMS = ["sampen", "apen", "apenv2"]

module_logger = logging.getLogger('tsanalyse.entropy')

# DATA TYPE DEFINITIONS
"""This is a data type defined to be used as a return for entropy; it
contains the number of points in the file, and the file's entropy"""
EntropyData = namedtuple('EntropyData', 'points entropy')


# ENTRY POINT FUNCTION
def entropy(input_name, entropy_type, dimension, tolerances, round_digits=None):
    """
    (str, str, int, float) -> EntropyData
    
    Given a file or directory named input_name, calculate the desired
    entropy to all the files.

    NOTE: This functions last two parameters are specific for the entropy 
    calculating algorithms we are using (both apen and sampen use the dimension
    and tolerance parameters.
    """

    method_to_call = getattr(sys.modules[__name__], entropy_type)
    entropy_dict = {}

    if os.path.isdir(input_name):
        filelist = util.listdir_no_hidden(input_name)
        for filename in filelist:
            try:
                entropy_data = method_to_call(os.path.join(input_name, filename.strip()), dimension,
                                              tolerances[filename], round_digits)
            except KeyError as ke:
                module_logger.error("Key %s does not exist in tolerances' list. Skipping file..." % ke)
            except ValueError as voe:
                module_logger.critical("%s. Skipping file..." % voe)
            except IndexError as ixe:
                module_logger.critical("%s - The file does not conform to the requisites: one column with the hrf vales. Skipping ..." % ixe)
            else:
                entropy_dict[filename.strip()] = entropy_data
    else:
        filename = os.path.basename(input_name)
        try:
            tolerances = tolerances[list(tolerances.keys())[0]]
        except IndexError as ixe:
            module_logger.error("%s on Tolerance's list." % ixe)
        else:
            try:
                entropy_data = method_to_call(input_name.strip(), dimension, tolerances, round_digits)
            except ValueError as voe:
                module_logger.critical("%s. Skipping file..." % voe)
            except IndexError as ixe:
                module_logger.critical("%s. Skipping file..." % ixe)
            else:
                entropy_dict[filename] = entropy_data
    # we will move this log to the interfaces to avoid "spam" when debugging multiscale
    # module_logger.debug("Entropy dictionary: {0}".format(entropy_dict))
    return entropy_dict


def calculate_std(input_name):
    """
    (str) -> dict of str : float

    Function to calculate the standard deviation for the values in a file/directory.
    Returns a dictionary that associate filenames to their respective std.
    
    """
    files_std = {}
    if os.path.isdir(input_name):
        filelist = util.listdir_no_hidden(input_name)
        for filename in filelist:
            # debug
            # print("calculate_file_st input: %s" % os.path.join(input_name, filename))
            try:
                files_std[filename] = calculate_file_std(os.path.join(input_name, filename))
            except ValueError as voe:
                module_logger.error("%s" % voe)
                module_logger.warning("Skipping file %s..." % filename)
    else:
        try:
            files_std[input_name] = calculate_file_std(input_name)
        except ValueError as voe:
            module_logger.error("%s" % voe)
            module_logger.warning("Skipping file %s..." % input_name)
    module_logger.debug("Files STD: {0}".format(files_std))
    return files_std


def calculate_file_std(filename):
    """
    (str) -> float

    Function to calculate the standard deviation of the values in a single file.

    """
    if util.is_empty_file(filename):
        raise ValueError("File '%s' is empty. Unable to compute standard deviation." % filename)
        # module_logger.warning("File %s is empty. Standard deviation will be set to 0." % filename)
        # return 0

    # with open(filename, "rU") as fdin:
    #     file_data = fdin.readlines()
    # file_data = list(map(float, file_data))

    # -1 to read the last available column
    file_data = util.readlines_with_col_index(filename, col_index=-1, as_type=float)
    # lets force a type cast to float so the error can be caught outside
    file_data = map(float, file_data)
    # print(file_data)

    module_logger.info("Computing std for file '%s'" % util.remove_project_path_from_file(filename))
    return numpy.std(file_data)


def sampen(filename, dimension, tolerance, round_digits=None):
    """
    (str, int, float) -> EntropyData

    Given a filename, calculate the sample entropy.

    NOTE: Pyeeg implementation
    """
    if util.is_empty_file(filename):
        raise ValueError("File %s is empty" % filename)

    # with open(filename, 'r') as file_d:
    #     file_data = file_d.readlines()
    # file_data = numpy.array(map(float, file_data))  # so file_data has attribute 'size' (due to pyeeg samp_entropy impl.)
    #

    # -1 to read the last available column
    file_data = util.readlines_with_col_index(filename, col_index=-1, as_type=float)
    # lets force a type cast to float so the error can be caught outside
    file_data = numpy.array(map(float, file_data))

    module_logger.info("Computing sample entropy for file '%s'" % util.remove_project_path_from_file(filename))

    try:
        samp_ent = samp_entropy(file_data, dimension, tolerance)
    except MemoryError:
        module_logger.critical("Memory Error while computing sample entropy. Ignoring file...")
        samp_ent = numpy.nan
        # raise MemoryError
    else:
        module_logger.debug("entropy: %s" % samp_ent)

        if round_digits:
            samp_ent = round(samp_ent, round_digits)

    return EntropyData(len(file_data), samp_ent)


# TODO: later evaluate this method for computational performance vs the one we have
def sampenv2(U, m, r):
    # wikipedia implementation
    def _maxdist(x_i, x_j):
        result = max([abs(ua - va) for ua, va in zip(x_i, x_j)])
        return result

    def _phi(m):
        x = [[U[j] for j in range(i, i + m - 1 + 1)] for i in range(N - m + 1)]
        C = [len([1 for j in range(len(x)) if i != j and _maxdist(x[i], x[j]) <= r]) for i in range(len(x))]
        return sum(C)

    N = len(U)

    return -numpy.log(_phi(m+1) / _phi(m))


# IMPLEMENTATION
def apen(filename, dimension, tolerance, round_digits=None):
    """
    (str, int, float) -> EntropyData

    Given a filename, calculate the aproximate entropy. 

    NOTE: Pyeeg implementation    
    """
    if util.is_empty_file(filename):
        raise ValueError("File %s is empty" % filename)

    # with open(filename, "r") as file_d:
    #     file_data = file_d.readlines()
    # # file_data = list(map(float, file_data))
    # file_data = numpy.array(map(float, file_data))  # so file_data has attribute 'size' (due to pyeeg samp_entropy impl.)

    # -1 to read the last available column
    file_data = util.readlines_with_col_index(filename, col_index=-1, as_type=float)
    # lets force a type cast to float so the error can be caught outside
    file_data = numpy.array(map(float, file_data))

    module_logger.info("Computing approximate entropy for file '%s'" % util.remove_project_path_from_file(filename))
    try:
        ap_ent = ap_entropy(file_data, dimension, tolerance)
    except MemoryError:
        module_logger.critical("Memory Error while computing approximate entropy. Ignoring file...")
        ap_ent = numpy.nan
    module_logger.debug("entropy: %s" % ap_ent)

    if round_digits:
        ap_ent = round(ap_ent, round_digits)

    return EntropyData(len(file_data), ap_ent)


def apenv2(filename, dimension, tolerance, round_digits=None):
    """
    (str, int, float) -> EntropyData
    
    An implementation of Approximate entropy. The explanation of the algorithm is
    a bit long because it is a little different from the original version it was 
    based on. Although it is still an O(mn2) worst case algorithm it tends to get
    better time by discarding some calculations.

    BIBLIGRAPHICAL REFERENCE:
    Fusheng, Y., Bo, H. and Qingyu, T. (2000) Approximate Entropy and Its 
    Application to Biosignal Analysis, in Nonlinear Biomedical Signal 
    Processing: Dynamic Analysis and Modeling, Volume 2 (ed M. Akay), John Wiley
    & Sons, Inc., Hoboken, NJ, USA. doi: 10.1002/9780470545379.ch3
        
    ALGORITHM: Based on the algorithm described in the book referenced, 
    this implementation actually calculates the n_m and n_m+1(n_mp) vectors directly.
    The following description is an explanation to help you understand why it is
    possible to jump directly to building n_m.
    
    Suppose we started by directly calculating the auxiliary matrix S where every
    cell S(i,j) is either 0 if the absolute distance between points i and j is 
    bigger then the tolerance or 1 otherwise. The matrix is symmetrical and the 
    diagonal is all 1's, so we would only actually need to calculate the upper half
    of the matrix.
    
    In matrix Crm the cell value will be one if all the S(i,j)...S(i+m,j+m) cells 
    are 1. Or we can look at it the other way around and say that if any of the
    values of that interval is 0 then Crm(i,j) is also 0, moreover if we start at
    the S(i+m,j+m) cell and work our way back if we find a 0 we know that any Crm 
    cells diagonally above that one will also be 0(*). Looking at the description 
    it's easy to see that we could just as easily star here, if instead of verifying
    the value of auxiliary matrix S is 0 we directly verify if the absolute distance
    is greater that tolerance. The Crm and Crm+1 matrices are necessarily also
    symmetrical and with a main diagonal filled with 1's.
    
    n_m, and n_m+1 are vectors where every index(i) is the sum of each row(i) in Crm
    and Crm+1 respectively. Since we proposed looking for 0's instead of 1 our N
    vectors start with the value assuming all the columns in the row are 1, we then
    subtract for every 0 found. Although the Cr matrices are not actually created
    the two variables i and j in the implementation are the row and column for the
    Crm matrix. With that in mind and the fact that the Crm matrix is symmetrical,
    we can simply test the value of the distance between points i and j, if it 
    is bigger than the tolerance, Crm would have a zero in that cell and so we 
    subtract one from our n_m and n_m+1 vector at position i and j. Provided of
    course both i and j are within the index limits.
    
    The rest of the implementation follows the description found it the book, c_m
    is the vector n_m with all cells divided by the length of n_m. Analogous for c_mp
    and n_mp. Finally the Phi's are calculated by averaging the c_m and c_mp vectors
    and the entropy value is the subtraction of Phi of c_m and Phi of c_mp.
    
    (*)As an implementation boost we use this knowledge to skip some cell whose value
    we already know to be 0. This is done by creating a burned_indexes that contains 
    the columns we want to jump over in the upcoming rows. The columns are kept 
    in a dictionary so the test if a particular column is to jumped is O(1).
    """

    if util.is_empty_file(filename):
        raise ValueError("File {0} is empty".format(filename))

    # -1 to read the last available column
    file_data = util.readlines_with_col_index(filename, col_index=-1, as_type=float)
    # lets force a type cast to float so the error can be caught outside
    file_data = list(map(float, file_data))
    module_logger.info("Computing approximate entropy (V2) for file '%s'" % util.remove_project_path_from_file(filename))

    data_len = len(file_data)

    try:
        n_m = [data_len - dimension + 1] * (data_len - dimension + 1)
        n_mp = [data_len - dimension] * (data_len - dimension)
        burned_indexes = [{} for i in range(data_len - dimension + 1)]

        for i in range(0, data_len - (dimension - 1)):
            if i > 0:
                burned_indexes[i - 1] = None
            for j in range(i + 1, data_len - (dimension - 1)):
                if j in burned_indexes[i]:
                    continue
                m = dimension - 1
                while m >= 0:
                    if abs(file_data[i + m] - file_data[j + m]) > tolerance:
                        mabove = m
                        while mabove >= 0:
                            if i + mabove < data_len - (dimension - 1) and j + mabove < data_len - (dimension - 1):
                                n_m[i + mabove] -= 1
                                n_m[j + mabove] -= 1
                            if i + mabove < data_len - dimension and j + mabove < data_len - dimension:
                                n_mp[i + mabove] -= 1
                                n_mp[j + mabove] -= 1
                            if i + mabove < data_len - dimension + 1 and j + mabove < data_len - dimension + 1:
                                burned_indexes[i + mabove][j + mabove] = None
                            mabove -= 1
                        break
                    m -= 1
                if m < 0 and i < data_len - dimension and j < data_len - dimension and abs(
                                file_data[i + dimension] - file_data[j + dimension]) > tolerance:
                    n_mp[i] -= 1
                    n_mp[j] -= 1

        c_m = [line / float(data_len - dimension + 1) for line in n_m]
        c_mp = [line / float(data_len - dimension) for line in n_mp]

        phi_m = numpy.mean([numpy.log(pos) for pos in c_m])
        phi_mp = numpy.mean([numpy.log(pos) for pos in c_mp])

        ap_en = phi_m - phi_mp
    except MemoryError:
        module_logger.critical("Memory Error while computing approximate entropy. Ignoring file...")
        ap_en = numpy.nan

    module_logger.debug("entropy: %s" % ap_en)
    if round_digits:
        ap_en = round(ap_en, round_digits)

    return EntropyData(len(file_data), ap_en)


# def fast_apen(filename,args):
#    """Try the implementation described in this article 
#    http://www.sciencedirect.com/science/article/pii/S0169260710002956"""
#
#    with open(filename,"r") as file_d:
#        file_data = file_d.readlines()
#    file_data = list(map(float,file_data))
#
#    data_len = len(file_data)
#
#    pointArray = transform_to_space(m,file_data)
#    
#    pointArray.sort()


# AUXILIARY FUNCTIONS
def is_entropy_table_empty(entropy_table):
    return all(map(lambda x: len(entropy_table[x]) < 1, entropy_table))


def add_parser_options(parser):
    """
    (argparse.ArgumentParser) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse parser or subparser,
    and are the optional arguments for the entry function in this module

    """
    # positional = parser.add_argument_group('positional arguments')
    parser.add_argument('-a', '--algorithm', dest="algorithm", action="store", metavar="ALGORITHM",  # required=True,
                            default='sampen',
                            help="Specifies the entropy algorithm to use. "
                             "Available algorithms: " + ", ".join(AVAILABLE_ALGORITHMS) + " . [default:%(default)s]")
    
    parser.add_argument('-sdt', '--sd-tolerance', dest="sd_tolerance", type=float, action="store", metavar="TOLERANCE",
                        help="Tolerance level (TOLERANCE x Standard Deviation) to be used when "
                             "calculating sample entropy. [default:%(default)s]",
                        default=0.15)
    parser.add_argument('-ut', '--unique-tolerance', dest="unique_tolerance", type=float, action="store", metavar="TOLERANCE",
                        help="Tolerance level to be used directly (without being multiplied by the Standard Deviation)"
                             " when calculating sample entropy.",
                        default=None)
    parser.add_argument('-d', '--dimension', dest="dimension", type=int, action="store", metavar="DIMENSION",
                        help="Matrix Dimension. [default:%(default)s]", default=2)
