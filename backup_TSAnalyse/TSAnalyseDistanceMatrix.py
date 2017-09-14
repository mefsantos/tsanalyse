#!/usr/bin/python

import os
import numpy
import csv
import argparse
import tools.distance
import tools.compress
import tools.entropy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="distanceMatrix")
    parser.add_argument('input_dir', metavar="INPUT DIRECTORY",
                        help='directory whose distance matrix will be calculated')

    subparsers = parser.add_subparsers(
            help='Different distance definition that can be used with compression and/or entropy ' +
                 '(.denotes the concatenation of two files)',
            dest="distance")

    tools.distance.add_parser_options(subparsers)

    args = parser.parse_args()
    options = vars(args)

    if options['input_dir'].endswith('/'):
        options['input_dir'] = options['input_dir'][:-1]

    file_list = os.listdir(options['input_dir'])
    nfiles = len(file_list)
    distances = numpy.zeros((nfiles, nfiles), float)

    # for now the only distance definitions available all use
    # compression, if I ever stumble upon one that uses entropy this
    # block will need to be changed
    options['level'] = tools.compress.set_level(options)
    if options['decompress']:
        out_file = "%s_decompress_%s_%d_%smatrix.csv" % (
            options['input_dir'], options['compressor'], options['level'], options['distance'])
    else:
        out_file = "%s_%s_%d_%smatrix.csv" % (
            options['input_dir'], options['compressor'], options['level'], options['distance'])
    row = 0
    while row < nfiles:
        column = 0
        while column < nfiles:
            if row != column:
                # print "Comparisons left",comparisons_left
                # comparisons_left -=1
                file1 = os.path.join(options['input_dir'], file_list[row])
                file2 = os.path.join(options['input_dir'], file_list[column])
                dist = tools.distance.distance(file1.strip(), file2.strip(), options['distance'], options['decompress'],
                                               options['compressor'], options['level'], )
                distances[row][column] = round(dist, 5)
            column += 1
        row += 1

    with open(out_file, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(file_list)
        writer.writerows(distances)
