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


# python setup.py install --user 

echo ""
echo "Adding PAQ8L and PPMD source files to PATH"
echo "#add paq8l and ppmd source files to PATH" >> ~/.bashrc
# echo "#add paq8l and ppmd source files to PATH" >> ~/.profile

PACKAGE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo export PATH='${PATH}':${PACKAGE_DIR}/algo/paq8l_src >> ~/.bashrc
echo export PATH='${PATH}':${PACKAGE_DIR}/algo/ppmd_src >> ~/.bashrc
echo -e "\n" >> ~/.bashrc

export PATH=$PATH:$PACKAGE_DIR/algo/paq8l_src
export PATH=$PATH:$PACKAGE_DIR/algo/ppmd_src

echo ""
echo "Done"


