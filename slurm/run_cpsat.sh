#!/bin/bash
#SBATCH --job-name=cpsat
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --time=12:00:00
#SBATCH --output=logs/cpsat_%x_%j.out
#SBATCH --error=logs/cpsat_%x_%j.err

# Usage (eine Groesse auf 5 Jobs aufteilen, je 20 Instanzen):
#   sbatch --job-name=cpsat_20x10_g1 slurm/run_cpsat.sh 20x10 0 19
#   sbatch --job-name=cpsat_20x10_g2 slurm/run_cpsat.sh 20x10 20 39
#   ... bis g5 mit 80 99
#
# Oder bequem alle 5 Gruppen auf einmal einreichen:
#   bash slurm/submit_cpsat_split.sh 20x10
#
# Oder mehrere Groessen gleichzeitig, je EIN Job pro Groesse (0..99):
#   bash slurm/submit_cpsat_sizes.sh 10x10 30x10 40x10 20x20 20x30
#
# Jeder Job verarbeitet nur einen Teilbereich der Instanzen, was die
# Anzahl gleichzeitig laufender Prozesse pro Node reduziert (siehe
# MAX_PARALLEL unten). Die Per-Instance CSV Dateien sind resumable, also
# kann ein abgebrochener Job einfach neu eingereicht werden.

SIZE=${1:?"Usage: sbatch run_cpsat.sh <SIZE> <START_IDX> <END_IDX>"}
START_IDX=${2:?"Usage: sbatch run_cpsat.sh <SIZE> <START_IDX> <END_IDX>"}
END_IDX=${3:?"Usage: sbatch run_cpsat.sh <SIZE> <START_IDX> <END_IDX>"}

mkdir -p logs results

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

PYTHON=/home/grafyann/master_thesis_env/bin/python
TIME_LIMIT=3600
CPUS=${SLURM_CPUS_PER_TASK:-40}

# Groessere Instanzen brauchen deutlich mehr RAM pro CP-SAT Solve. Bei
# fixer MAX_PARALLEL=10 fuehrte das bei 200x10 zu Speicherueberlastung
# und "double free or corruption" Abstuerzen (Heap-Corruption unter
# OOM-Druck), zusaetzlich verschaerft dadurch dass CP-SAT ohne explizites
# num_search_workers-Limit versucht, alle CPUs des Nodes zu nutzen -> mit
# 10 parallelen Prozessen massives Thread-Oversubscription.
case "$SIZE" in
    200x10|20x20|20x30)
        MAX_PARALLEL=4
        ;;
    *)
        MAX_PARALLEL=10
        ;;
esac

# CP-SAT Threads pro Instanz begrenzen, damit MAX_PARALLEL Prozesse
# zusammen nicht mehr Threads als CPUS anfordern.
NUM_WORKERS=$(( CPUS / MAX_PARALLEL ))
if (( NUM_WORKERS < 1 )); then
    NUM_WORKERS=1
fi

PER_INSTANCE_DIR="results/CP_SAT/${SIZE}/per_instance"
MASTER_CSV="results/CP_SAT/${SIZE}.csv"
mkdir -p "$PER_INSTANCE_DIR"

echo "=== CP-SAT $SIZE (idx ${START_IDX}-${END_IDX}, max_parallel=$MAX_PARALLEL, num_workers=$NUM_WORKERS, time_limit=${TIME_LIMIT}s): starting $(date) ==="

for i in $(seq $START_IDX $END_IDX); do
    $PYTHON run_cpsat_only.py --size $SIZE --instance_idx $i --time_limit $TIME_LIMIT --num_workers $NUM_WORKERS &
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