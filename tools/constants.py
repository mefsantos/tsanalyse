"""
Copyright (C) 2018 Marcelo Santos

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

This module implements several utility functions to extend python's functionality, enabling verbosity and
 self explanatory code.


MODULE EXTERNAL DEPENDENCIES:

ENTRY POINT: NONE

"""
import os


# might need to set these at runtime when each interface is load so we get the exact (and correct) path
TSA_HOME = os.path.abspath(".")
TSFILTER_PATH = os.path.join(TSA_HOME, "TSFilter.py")
TSADIRECT_PATH = os.path.join(TSA_HOME, "TSAnalyseDirect.py")
TSAMULTISCALE_PATH = os.path.join(TSA_HOME, "TSAnalyseMultiScale.py")
TSAFILEBLOCKS_PATH = os.path.join(TSA_HOME, "TSAnalyseFileBlocks.py")

TMP_DIR = os.path.join(TSA_HOME, "tmp")
RUN_ISOLATED_FILES_PATH = os.path.join(TSA_HOME, "individual_runs")
BLOCK_ANALYSIS_OUTPUT_PATH = os.path.join(TSA_HOME, "block_analysis")
FILE_BLOCKS_STORAGE_PATH = os.path.join(TSA_HOME, "file_blocks")
STV_ANALYSIS_STORAGE_PATH = os.path.join(TSA_HOME, "stv_analysis")

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_CUTOFF_LIMITS = [50,250]
