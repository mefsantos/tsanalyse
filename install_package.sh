#! /bin/bash

echo "Installing Python Package"

python setup.py install --user 

echo ""
echo "Adding PAQ8L and PPMD source files to PATH"
echo "#add paq8l and ppmd source files to PATH" >> ~/.bashrc
# echo "#add paq8l and ppmd source files to PATH" >> ~/.profile

PACKAGE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


echo export PATH='${PATH}':${PACKAGE_DIR}/algo/paq8l_src >> ~/.bashrc
echo export PATH='${PATH}':${PACKAGE_DIR}/algo/ppmd_src >> ~/.bashrc
echo -e "\n" >> ~/.bashrc


# echo export PATH='${PATH}':${PACKAGE_DIR}/algo/paq8l_src >> ~/.profile
# echo export PATH='${PATH}':${PACKAGE_DIR}/algo/ppmd_src >> ~/.profile
# echo -e "\n" >> ~/.profile

# # Reload profile to update environment
source $HOME/.bashrc # doesnt work


echo ""
echo "Done"

bash

