#!/bin/bash
#SBATCH --job-name=cpsat_missing
#SBATCH --account=def-cglee
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --time=04:00:00
#SBATCH --output=logs/cpsat_missing_%x_%j.out
#SBATCH --error=logs/cpsat_missing_%x_%j.err

# Usage: sbatch --job-name=cpsat_missing_50x10 slurm/run_cpsat_missing.sh 50x10
SIZE=${1}

if [[ -z "$SIZE" ]]; then
    echo "ERROR: Usage: sbatch slurm/run_cpsat_missing.sh SIZE"
    exit 1
fi

mkdir -p logs results/CP_SAT/$SIZE/per_instance

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

PYTHON=/home/grafyann/master_thesis_env/bin/python
MAX_PARALLEL=10
TIME_LIMIT=3600

echo "=== Finding missing instances for $SIZE ==="
MISSING=$($PYTHON find_missing.py --size $SIZE --verbose 2>/dev/null)

if [[ -z "$MISSING" ]]; then
    echo "Nothing to do, all instances completed."
    exit 0
fi

echo "=== Running missing instances ==="
echo "Indices: $MISSING"
echo "MAX_PARALLEL=$MAX_PARALLEL, TIME_LIMIT=$TIME_LIMIT"
echo "Start time: $(date)"

# Use a temp directory as a semaphore to count running jobs reliably.
# Each running job creates a lock file. We count lock files instead of
# relying on 'jobs -r -p' which does not work correctly under SLURM.
LOCKDIR=$(mktemp -d)

run_instance() {
    local idx=$1
    echo "[$(date +%H:%M:%S)] Starting instance_idx=$idx"
    $PYTHON run_cpsat_only.py --size $SIZE --instance_idx $idx --time_limit $TIME_LIMIT
    rm -f "$LOCKDIR/lock_$idx"
}

for idx in $MISSING; do
    # Wait until fewer than MAX_PARALLEL lock files exist.
    while [[ $(ls "$LOCKDIR" | wc -l) -ge $MAX_PARALLEL ]]; do
        sleep 2
    done
    touch "$LOCKDIR/lock_$idx"
    run_instance $idx &
done

wait
rm -rf "$LOCKDIR"

echo ""
echo "=== CP-SAT missing instances finished for $SIZE ==="
echo "End time: $(date)"

echo ""
echo "=== Final status check ==="
$PYTHON find_missing.py --size $SIZE --verbose