#!/bin/bash
#SBATCH --job-name=baselines_cpsat_200x10
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:40:00
#SBATCH --array=0-99
#SBATCH --output=logs/cpsat_200x10_%A_%a.out
#SBATCH --error=logs/cpsat_200x10_%A_%a.err

mkdir -p logs results
python run_baselines.py --method CP_SAT --size 200x10 --instance_idx $SLURM_ARRAY_TASK_ID
