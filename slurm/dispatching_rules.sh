#!/bin/bash
#SBATCH --job-name=baselines_dr
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=logs/dr_%j.out
#SBATCH --error=logs/dr_%j.err

mkdir -p logs results

for METHOD in FIFO SPT MOR MWR; do
    for SIZE in 20x10 50x10 100x10 200x10; do
        python run_baselines.py --method $METHOD --size $SIZE
    done
done
