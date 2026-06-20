#!/bin/bash
# Alle Baseline Jobs fuer Trillium einreichen.
# Total: 3 Jobs (je 1 Node).
#
# Falls QOS Limit eng ist, einzeln einreichen:
#   sbatch slurm/dispatching_rules.sh    # fertig in Minuten
#   sbatch slurm/run_cpsat.sh            # bis ~4h
#   sbatch slurm/run_ga.sh               # bis ~2h

mkdir -p logs results

DR_JOB=$(sbatch --parsable slurm/dispatching_rules.sh)
echo "Dispatching rules: job $DR_JOB"

CPSAT_JOB=$(sbatch --parsable slurm/run_cpsat.sh)
echo "CP-SAT (all sizes): job $CPSAT_JOB"

GA_JOB=$(sbatch --parsable slurm/run_ga.sh)
echo "GA (all sizes): job $GA_JOB"

echo ""
echo "Submitted 3 jobs total. Monitor with: squeue -u \$USER"
