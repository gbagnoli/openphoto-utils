#!/bin/bash

version=$(python --version 2>&1)

echo $version | grep -q "3.3"
if [ $? -eq 0 ];then
    python -m unittest discover -s tests
else
    echo $version | grep -q "3.2"
    if [ $? -eq 0 ]; then
        pip install mock --use-mirrors 2>&1 >/dev/null
        python -m unittest discover -s tests
    else
        pip install argparse unittest2 mock --use-mirrors 2>&1 > /dev/null
        unit2 discover -s tests
    fi
fi
