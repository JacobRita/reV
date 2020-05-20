#!/bin/bash

set -e

PKG_NAME=nrel-rev

PY_VERSION=( 3.7 )

export CONDA_BLD_PATH=~/conda-bld

platforms=( osx-64 linux-64 win-64 )
for py in "${PY_VERSION[@]}"
do
	conda build conda.recipe/ --python=$py --channel=nrel
    file=$(conda build conda.recipe/ --python=$py --output)
    echo Building $file
    for platform in "${platforms[@]}"
    do
       conda convert -f --platform $platform $file -o $CONDA_BLD_PATH/
    done
done

# upload packages to conda
find $CONDA_BLD_PATH/ -name $PKG_NAME*.tar.bz2 | while read file
do
    echo Uploading $file
    anaconda upload -u nrel $file
done

echo "Building and uploading conda package done!"
rm -rf $CONDA_BLD_PATH/*
ls $CONDA_BLD_PATH