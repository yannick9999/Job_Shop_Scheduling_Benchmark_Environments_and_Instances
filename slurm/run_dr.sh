#!/bin/bash
#SBATCH --job-name=baselines_dr
#SBATCH --account=def-cglee
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --output=logs/dr_%j.out
#SBATCH --error=logs/dr_%j.err

mkdir -p logs results

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

PYTHON=/home/grafyann/master_thesis_env/bin/python

echo "=== Starting dispatching rules ==="
echo "Start time: $(date)"

for METHOD in FIFO SPT MOR MWR; do
    for SIZE in 20x10 50x10 100x10 200x10; do
        $PYTHON run_dr.py --method $METHOD --size $SIZE &
    done
done

wait

echo "=== Dispatching rules finished ==="
echo "End time: $(date)"