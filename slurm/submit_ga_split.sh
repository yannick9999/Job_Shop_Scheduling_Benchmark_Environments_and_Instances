#!/bin/bash
# Submit 5 GA jobs, each covering 20 instances.
# Usage: bash slurm/submit_ga_split.sh 20x10
#        bash slurm/submit_ga_split.sh 50x10
#        bash slurm/submit_ga_split.sh 100x10

SIZE=${1}

if [[ -z "$SIZE" ]]; then
    echo "ERROR: Usage: bash slurm/submit_ga_split.sh SIZE"
    echo "       Example: bash slurm/submit_ga_split.sh 20x10"
    exit 1
fi

mkdir -p logs results/GA

echo "Submitting GA jobs for $SIZE..."

sbatch --job-name=ga_${SIZE}_g1 slurm/run_ga.sh $SIZE  0 19
sbatch --job-name=ga_${SIZE}_g2 slurm/run_ga.sh $SIZE 20 39
sbatch --job-name=ga_${SIZE}_g3 slurm/run_ga.sh $SIZE 40 59
sbatch --job-name=ga_${SIZE}_g4 slurm/run_ga.sh $SIZE 60 79
sbatch --job-name=ga_${SIZE}_g5 slurm/run_ga.sh $SIZE 80 99

echo ""
echo "Submitted 5 jobs for GA $SIZE. Monitor with: squeue --me"
echo "Check progress: ls results/GA/ | grep $SIZE"