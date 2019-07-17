#!/usr/bin/env bash
repoDir=$(git rev-parse --show-toplevel)
cd "$repoDir/.git/hooks"
files=$( find "$repoDir/hooks/" -name "*" |  # find files
grep -e "/(applypatch-msg\|commit-msg\|post-update\|pre-applypatch\|pre-commit\|pre-push\|pre-rebase\|pre-receive\|prepare-commit-msg\|update)$" |  # check if valid
sed -E "s/^(.*)$/\"\1\" /g" |  # add quotes
sed ":a;N;s/\n/ /g;ba")  # replace newline by space
declare -a array="( $files )"
for file in "${array[@]}"  # iterate over valid files
do
    ln -s "$file"  # create symlink in .git/hooks
done
