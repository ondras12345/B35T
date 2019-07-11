#!/usr/bin/env bash
repoDir=$(git rev-parse --show-toplevel)
bandit -r --exclude $repoDir/.git,$repoDir/B35t_reader $repoDir
