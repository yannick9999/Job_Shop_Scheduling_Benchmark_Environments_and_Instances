#!/bin/bash
#SBATCH --job-name=cpsat
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --time=08:00:00
#SBATCH --output=logs/cpsat_%x_%j.out
#SBATCH --error=logs/cpsat_%x_%j.err

# Usage:
#   sbatch --job-name=cpsat_20x10_g1 slurm/run_cpsat.sh 20x10 0 19
#   sbatch --job-name=cpsat_20x10_g2 slurm/run_cpsat.sh 20x10 20 39
#   ... bis g5 mit 80 99
#
# Oder bequem alle 5 Gruppen auf einmal einreichen:
#   bash slurm/submit_cpsat_split.sh 20x10
#
# Jeder Job verarbeitet nur einen Teilbereich der 100 Instanzen, was die
# Anzahl gleichzeitig laufender Prozesse pro Node reduziert. Die Per-Instance
# CSV Dateien sind resumable, also kann ein abgebrochener Job einfach neu
# eingereicht werden.

SIZE=${1:?"Usage: sbatch run_cpsat.sh <SIZE> <START_IDX> <END_IDX>"}
START_IDX=${2:?"Usage: sbatch run_cpsat.sh <SIZE> <START_IDX> <END_IDX>"}
END_IDX=${3:?"Usage: sbatch run_cpsat.sh <SIZE> <START_IDX> <END_IDX>"}

mkdir -p logs results

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

PYTHON=/home/grafyann/master_thesis_env/bin/python
MAX_PARALLEL=10
TIME_LIMIT=3600

PER_INSTANCE_DIR="results/CP_SAT/${SIZE}/per_instance"
MASTER_CSV="results/CP_SAT/${SIZE}.csv"
mkdir -p "$PER_INSTANCE_DIR"

echo "=== CP-SAT $SIZE (idx ${START_IDX}-${END_IDX}, max_parallel=$MAX_PARALLEL, time_limit=${TIME_LIMIT}s): starting $(date) ==="

for i in $(seq $START_IDX $END_IDX); do
    $PYTHON run_cpsat_only.py --size $SIZE --instance_idx $i --time_limit $TIME_LIMIT &
    while (( $(jobs -rp | wc -l) >= MAX_PARALLEL )); do
        sleep 5
    done
done

wait

echo "=== CP-SAT $SIZE (idx ${START_IDX}-${END_IDX}): all instances finished $(date) ==="

# Merge alle per_instance CSVs zu einer Master CSV. Wenn andere Jobs noch
# laufen, ist der Merge unvollstaendig. Sobald der letzte Job fertig ist,
# enthaelt die Master CSV alle Instanzen.
echo "instance_name,makespan,runtime_seconds,status,lower_bound" > "$MASTER_CSV"
for f in "$PER_INSTANCE_DIR"/*.csv; do
    if [ -f "$f" ]; then
        tail -n +2 "$f" >> "$MASTER_CSV"
    fi
done

N_RESULTS=$(($(wc -l < "$MASTER_CSV") - 1))
echo "=== Merged $N_RESULTS instances into $MASTER_CSV ==="

scontrol show job $SLURM_JOB_ID
sacct -j $SLURM_JOB_ID