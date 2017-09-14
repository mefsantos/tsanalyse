#! /bin/bash

echo "Setting up the Python Environment"

sudo apt-get update
# install librarires for 32-bit dependencies
sudo apt-get -y install lib32z1
sudo apt-get -y install lib32stdc++6

echo "Installing Python dependencies"
sudo apt-get install -y python-pip python-dev build-essential
sudo pip install --upgrade pip
sudo pip install --upgrade virtualenv
sudo pip install scipy numpy pylzma brotli pandas coveralls pytest-cov psutil

# echo "Installing Matlab to Python converter"
# sudo easy_install smop

echo "Setting up the default PATH"
PATH="/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin"

echo "Adding PAQ8L and PPMD source files to PATH"
echo "#add paq8l and ppmd source files to PATH" >> ~/.bashrc
echo "#add paq8l and ppmd source files to PATH" >> ~/.profile

PACKAGE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo export PATH='"'$PACKAGE_DIR/algo/paq8l_src:'$PATH''"' >> ~/.bashrc
echo export PATH='"'$PACKAGE_DIR/algo/ppmd_src:'$PATH''"' >> ~/.bashrc
echo -e "\n" >> ~/.bashrc

# uncomment if using a different terminal than bash
# echo export PATH='"'$PACKAGE_DIR/algo/paq8l_src:'$PATH''"' >> ~/.profile
# echo export PATH='"'$PACKAGE_DIR/algo/ppmd_src:'$PATH''"' >> ~/.profile
# echo -e "\n" >> ~/.profile

# Reload bashrc and profile to set PATH"
bash --login; exit
