#!/bin/bash
#SBATCH --job-name=ga_%x
#SBATCH --account=def-cglee
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=24:00:00
#SBATCH --output=logs/ga_%x_%j.out
#SBATCH --error=logs/ga_%x_%j.err

# Usage: sbatch --job-name=ga_20x10_g1 slurm/run_ga.sh 20x10 0 19
SIZE=${1}
START_IDX=${2}
END_IDX=${3}

if [[ -z "$SIZE" || -z "$START_IDX" || -z "$END_IDX" ]]; then
    echo "ERROR: Usage: sbatch slurm/run_ga.sh SIZE START_IDX END_IDX"
    exit 1
fi

mkdir -p logs results/GA

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

PYTHON=/home/grafyann/master_thesis_env/bin/python

echo "=== GA: $SIZE instances $START_IDX-$END_IDX ==="
echo "Start time: $(date)"

# Multiprocessing is disabled by default (opt-in with --multiprocessing).
# Parallelism comes from 5 jobs running simultaneously via submit_ga_split.sh.
$PYTHON run_ga.py \
    --size $SIZE \
    --start_idx $START_IDX \
    --end_idx $END_IDX \
    --time_limit 3600

echo "=== GA finished: $SIZE $START_IDX-$END_IDX ==="
echo "End time: $(date)"