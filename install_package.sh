#! /bin/bash

echo "Installing Python Package"

if [ -z $1 ];
then
	python setup.py install --user 
else
	if [ $1 == "sudo" ] || [ $1 == "su" ] || [ $1 == "root" ];
	then
	sudo python setup.py install
	else
	python setup.py install --user 
	fi
fi

echo ""

#PACKAGE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#PACKAGE_DIR="$(dirname ${BASH_SOURCE[0]})"

cd "$(dirname -- "$0")"
PACKAGE_DIR="$PWD"
cd - > /dev/null

# only add to bashrc if path does not exists in $PATH
if ! echo $PATH | grep -Fq "/algo/paq8l_src"
then
	echo "Adding PAQ8L source files to PATH"
	echo "" >> ~/.bashrc
	echo "# PAQ8L" >> ~/.bashrc
	echo export PATH='${PATH}':${PACKAGE_DIR}/algo/paq8l_src >> ~/.bashrc
	export PATH=$PATH:$PACKAGE_DIR/algo/paq8l_src
fi

if ! echo $PATH | grep -Fq "/algo/ppmd_src"
then
	echo "Adding PPMD source files to PATH"
	echo "" >> ~/.bashrc
	echo "# PPMD" >> ~/.bashrc
	echo export PATH='${PATH}':${PACKAGE_DIR}/algo/ppmd_src >> ~/.bashrc
	export PATH=$PATH:$PACKAGE_DIR/algo/ppmd_src
fi

echo ""
echo "Done"
echo ""

