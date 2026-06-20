#!/bin/bash
#SBATCH --job-name=baselines_cpsat
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --time=06:00:00
#SBATCH --output=logs/cpsat_all_%j.out
#SBATCH --error=logs/cpsat_all_%j.err

# Trillium gibt einen ganzen 192-Core Node.
# CP-SAT braucht 2 Cores pro Instanz, also 96 parallel.
# 100 Instanzen / 96 parallel = 2 Durchgaenge pro Groesse.
# 4 Groessen x 2 Durchgaenge x 30 min (time_limit) = ~4h worst case.
# Walltime 6h mit Puffer.

mkdir -p logs results

export PYTHONPATH="${SLURM_SUBMIT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export MPLCONFIGDIR=/scratch/grafyann/matplotlib_cache
mkdir -p $MPLCONFIGDIR

PYTHON=/home/grafyann/master_thesis_env/bin/python
MAX_PARALLEL=96

run_size() {
    local SIZE=$1
    echo "=== CP-SAT $SIZE: starting $(date) ==="

    for i in $(seq 0 99); do
        $PYTHON run_baselines.py --method CP_SAT --size $SIZE --instance_idx $i &

        # Warten falls Parallelitaetslimit erreicht
        while (( $(jobs -rp | wc -l) >= MAX_PARALLEL )); do
            sleep 5
        done
    done

    # Warten bis alle Instanzen dieser Groesse fertig sind
    wait
    echo "=== CP-SAT $SIZE: finished $(date) ==="
}

for SIZE in 20x10 50x10 100x10 200x10; do
    run_size $SIZE
done

echo "=== All CP-SAT jobs finished ==="
