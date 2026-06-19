#!/bin/bash
#SBATCH --job-name=baselines_dr
#SBATCH --partition=compute
#SBATCH --cpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --output=logs/dr_%j.out
#SBATCH --error=logs/dr_%j.err

mkdir -p logs results

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

for METHOD in FIFO SPT MOR MWR; do
    for SIZE in 20x10 50x10 100x10 200x10; do
        /home/grafyann/master_thesis_env/bin/python run_baselines.py --method $METHOD --size $SIZE
    done
done
