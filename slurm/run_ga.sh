#!/bin/bash
#SBATCH --job-name=baselines_ga
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --time=03:00:00
#SBATCH --output=logs/ga_all_%j.out
#SBATCH --error=logs/ga_all_%j.err

# Trillium gibt einen ganzen 192-Core Node.
# GA braucht 1 Core pro Instanz, also alle 100 gleichzeitig.
# 4 Groessen x 1 Durchgang x 30 min (time_limit) = ~2h worst case.
# Walltime 3h mit Puffer.

mkdir -p logs results

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

PYTHON=/home/grafyann/master_thesis_env/bin/python
MAX_PARALLEL=192

run_size() {
    local SIZE=$1
    echo "=== GA $SIZE: starting $(date) ==="

    for i in $(seq 0 99); do
        $PYTHON run_baselines.py --method GA --size $SIZE --instance_idx $i &

        while (( $(jobs -rp | wc -l) >= MAX_PARALLEL )); do
            sleep 5
        done
    done

    wait
    echo "=== GA $SIZE: finished $(date) ==="
}

for SIZE in 20x10 50x10 100x10 200x10; do
    run_size $SIZE
done

echo "=== All GA jobs finished ==="
