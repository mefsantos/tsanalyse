#! /bin/bash

# set DS_PATH to the directory of the data set you want to evaluate
DS_PATH="/home/msantos/Desktop/traces_individual_test/Traces_clean"




## to run individually for each file uncomment the following lines

#for f in $DS_PATH
#do
#	# take action on each file. $f store current file name
#	echo "./HRFAnalyseDirect.py $f entropy apen -t 0.1"
#	./HRFAnalyseDirect.py $f entropy apen -t 0.1
#done



# # entropy
echo "./HRFAnalyseDirect.py $DS_PATH entropy apen -t 0.1"
./HRFAnalyseDirect.py $DS_PATH entropy apen -t 0.1

echo "./HRFAnalyseDirect.py $DS_PATH entropy apen -t 0.15"
./HRFAnalyseDirect.py $DS_PATH entropy apen -t 0.15

echo "./HRFAnalyseDirect.py $DS_PATH entropy apen -t 0.2"
./HRFAnalyseDirect.py $DS_PATH entropy apen -t 0.2


echo "./HRFAnalyseDirect.py $DS_PATH entropy sampen -t 0.1"
./HRFAnalyseDirect.py $DS_PATH entropy sampen -t 0.1

echo "./HRFAnalyseDirect.py $DS_PATH entropy sampen -t 0.15"
./HRFAnalyseDirect.py $DS_PATH entropy sampen -t 0.15

echo "./HRFAnalyseDirect.py $DS_PATH entropy sampen -t 0.2"
./HRFAnalyseDirect.py $DS_PATH entropy sampen -t 0.2


# to use compression uncomment the following lines

echo "./HRFAnalyseDirect.py $DS_PATH compress -c lzma --level 1"
./HRFAnalyseDirect.py $DS_PATH compress -c lzma --level 1

echo "./HRFAnalyseDirect.py $DS_PATH compress -c ppmd --level 1"
./HRFAnalyseDirect.py $DS_PATH compress -c ppmd --level 1

echo "./HRFAnalyseDirect.py $DS_PATH compress -c gzip --level 1"
./HRFAnalyseDirect.py $DS_PATH compress -c gzip --level 1

echo "./HRFAnalyseDirect.py $DS_PATH compress -c bzip2 --level 1"
./HRFAnalyseDirect.py $DS_PATH compress -c bzip2 --level 1

echo "./HRFAnalyseDirect.py $DS_PATH compress -c brotli --level 1"
./HRFAnalyseDirect.py $DS_PATH compress -c brotli --level 1

echo "./HRFAnalyseDirect.py $DS_PATH compress -c paq8l --level 1"
./HRFAnalyseDirect.py $DS_PATH compress -c paq8l --level 1
