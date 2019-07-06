#!/usr/bin/env bash
thisDir=$(git rev-parse --show-toplevel)
cd $thisDir
flake8 --exclude .git,B35t_reader/B35T.py --max-line-length 119
cd - > /dev/null  # go back to previous directory
