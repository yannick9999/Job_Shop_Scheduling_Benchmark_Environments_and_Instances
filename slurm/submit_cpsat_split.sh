#!/bin/bash
# Reicht 5 CP-SAT Jobs ein, jeder mit 20 Instanzen.
#
# Usage:
#   bash slurm/submit_cpsat_split.sh 20x10
#   bash slurm/submit_cpsat_split.sh 50x10
#   bash slurm/submit_cpsat_split.sh 100x10
#   bash slurm/submit_cpsat_split.sh 200x10

SIZE=${1:?"Usage: bash submit_cpsat_split.sh <SIZE>"}

echo "Reiche 5 Jobs fuer Groesse $SIZE ein..."

for g in 1 2 3 4 5; do
    START=$(( (g - 1) * 20 ))
    END=$(( g * 20 - 1 ))
    JOB_NAME="cpsat_${SIZE}_g${g}"
    echo "  Job $g: instances ${START}-${END}"
    sbatch --job-name=$JOB_NAME slurm/run_cpsat.sh $SIZE $START $END
done

echo "Done. Pruefe mit: squeue --me"