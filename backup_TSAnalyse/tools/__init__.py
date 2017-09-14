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

Tools:
clean -- Remove unnecessary data from files

compression -- Compression algorithms deployment 

distance -- Calculate the distance between two files

entropy -- Application of pyeeg and other tool to data to determine entropy

multiscale -- construction and calls for multiscale.

partition -- File partition -- partition a file in blocks or cut of a chunk of the file using either minutes or lines.

pyeeg -- an entropy library made available by Forrest S. Bao, Xin Liu and Christina Zhang,
        "PyEEG: An Open Source Python Module for EEG/MEG Feature Extraction,"
        Computational Intelligence and Neuroscience, March, 2011

separate_blocks -- Using some metric define upper and lower limits and
                mark block that are above upper limits or below lower limits.

confidenceIntervalWithSlopeAnalysis -- evaluates the dataset containing multiscale analysis provided
                                        as input (file or directory), computes confidence intervals for each scale
                                        and performs a slope analysis within every scale using least squares regression.

compressionRatio -- Computes the compression ratio for a multiscale compression analysis.

csv2txsp3 -- Converts Comma-Separated Values (CSV) files into into SisPorto input format (TxSP3) files.

recordDuration -- Computes the duration of the signal contained in the input dataset.

clampageStateAnalysis -- Provides a deep analysis of compression and entropy by state regarding the analysis
                        of a clampage procedure.

utilityFunctions -- several utility functions to extend the python functionality and simple formulas used within
                    the modules of the package.

longitBaseAnalysis --  used to evaluate the confidence intervals of a high dimensionality dataset.
                    It allows a more specific analysis by creating nested groups within the dataset
                     based on multiple input parameters.


"""
# TODO: add declaration of the functions implemented (compressRatio, dsduration, ...)
