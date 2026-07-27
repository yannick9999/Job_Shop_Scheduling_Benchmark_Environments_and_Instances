#!/bin/bash
# Reicht fuer jede angegebene Groesse GENAU EINEN Job ein, der alle
# Instanzen dieser Groesse (0..N-1) verarbeitet. Damit koennen bis zu 5
# Groessen gleichzeitig laufen (ein Job pro Groesse), ohne dass man
# nacheinander pruefen muss, ob die vorherige Groesse schon fertig ist.
#
# Usage:
#   bash slurm/submit_cpsat_sizes.sh 10x10 30x10 40x10 20x20 20x30
#
# Slurm erlaubt hier maximal 5 gleichzeitige Jobs, also maximal 5
# Groessen auf einmal uebergeben. Fuer weniger Groessen einfach weniger
# Argumente angeben.

PYTHON=/home/grafyann/master_thesis_env/bin/python

if [[ $# -eq 0 ]]; then
    echo "Usage: bash slurm/submit_cpsat_sizes.sh <SIZE1> [SIZE2] ... (max 5)"
    exit 1
fi
if [[ $# -gt 5 ]]; then
    echo "ERROR: max 5 Groessen gleichzeitig (Slurm Job-Limit), du hast $# angegeben."
    exit 1
fi

echo "Reiche je einen Job fuer folgende Groessen ein: $*"

for SIZE in "$@"; do
    N=$($PYTHON -c "from run_cpsat_only import get_instances; print(len(get_instances('${SIZE}')))" 2>/dev/null)
    if [[ -z "$N" || "$N" -eq 0 ]]; then
        echo "  ERROR: keine Instanzen fuer Groesse $SIZE gefunden, ueberspringe."
        continue
    fi
    END=$((N - 1))
    JOB_NAME="cpsat_${SIZE}"
    echo "  Job fuer $SIZE: instances 0-${END} (${N} total)"
    sbatch --job-name=$JOB_NAME slurm/run_cpsat.sh $SIZE 0 $END
done

echo "Done. Pruefe mit: squeue --me"
