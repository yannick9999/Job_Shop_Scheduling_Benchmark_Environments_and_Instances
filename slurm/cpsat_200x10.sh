#!/bin/bash
#SBATCH --job-name=baselines_cpsat_200x10
#SBATCH --partition=compute
#SBATCH --cpus-per-task=2
#SBATCH --time=00:40:00
#SBATCH --array=0-99
#SBATCH --output=logs/cpsat_200x10_%A_%a.out
#SBATCH --error=logs/cpsat_200x10_%A_%a.err

mkdir -p logs results

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

/home/grafyann/master_thesis_env/bin/python run_baselines.py --method CP_SAT --size 200x10 --instance_idx $SLURM_ARRAY_TASK_ID
