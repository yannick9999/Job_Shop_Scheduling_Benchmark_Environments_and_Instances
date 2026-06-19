#!/bin/bash
# Submit all baseline evaluation jobs

mkdir -p logs results

# 1) Dispatching rules (fast, one job)
DR_JOB=$(sbatch --parsable slurm/dispatching_rules.sh)
echo "Dispatching rules: job $DR_JOB"

# 2) CP-SAT per size
for SIZE in 20x10 50x10 100x10 200x10; do
    CPSAT_JOB=$(sbatch --parsable slurm/cpsat_${SIZE}.sh)
    echo "CP-SAT $SIZE: job $CPSAT_JOB"
done

# 3) GA per size
for SIZE in 20x10 50x10 100x10 200x10; do
    GA_JOB=$(sbatch --parsable slurm/ga_${SIZE}.sh)
    echo "GA $SIZE: job $GA_JOB"
done
