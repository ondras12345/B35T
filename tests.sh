#!/usr/bin/env bash
repoDir=$(git rev-parse --show-toplevel)
cd "$repoDir"
printf '========== flake8 ==========\n'
./tests/linters/flake.sh
printf '\n========== bandit ==========\n'
./tests/linters/bandit.sh
printf '\n========== tests  ==========\n'
# https://stackoverflow.com/questions/1251999/how-can-i-replace-a-newline-n-using-sed
# | sed -E ':a;N;s/testing: ((\s?\S{1,}){1,})( ){2,}True\n/\1, /g;ba'
python -m unittest discover -s tests/unit
printf '\n'
read -p 'Press any key to continue'
