#!/bin/bash
#SBATCH --job-name=baselines_ga_200x10
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:40:00
#SBATCH --array=0-99
#SBATCH --output=logs/ga_200x10_%A_%a.out
#SBATCH --error=logs/ga_200x10_%A_%a.err

mkdir -p logs results
python run_baselines.py --method GA --size 200x10 --instance_idx $SLURM_ARRAY_TASK_ID
