#!/bin/bash
#SBATCH --job-name=baselines_ga_100x10
#SBATCH --partition=compute
#SBATCH --cpus-per-task=1
#SBATCH --time=00:40:00
#SBATCH --array=0-99
#SBATCH --output=logs/ga_100x10_%A_%a.out
#SBATCH --error=logs/ga_100x10_%A_%a.err

mkdir -p logs results

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

/home/grafyann/master_thesis_env/bin/python run_baselines.py --method GA --size 100x10 --instance_idx $SLURM_ARRAY_TASK_ID
