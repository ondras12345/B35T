#!/usr/bin/env bash
repoDir=$(git rev-parse --show-toplevel)
cd "$repoDir/B35T_reader"
if [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ] || [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then
    echo "Creating windows batch file"
    echo "mklink /D \"$repoDir/B35T_reader/B35T\" \"$repoDir/B35T\"" >> create-symlink-windows.bat
    echo "pause" >> create-symlink-windows.bat
    read -p "This script will now exit. Run the .bat file as administartor  "
else
    ln -s -d "$repoDir/B35T"
fi
