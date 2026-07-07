"""
Schlanker CP-SAT Entry-Point ohne PyTorch.

Wird von slurm/run_cpsat.sh aufgerufen. Schreibt eine separate CSV Datei pro
Instanz unter results/CP_SAT/{size}/per_instance/. Existiert die Datei bereits,
wird die Instanz uebersprungen, das macht den Job resumable.

Beispiel:
    python run_cpsat_only.py --size 20x10 --instance_idx 0 --time_limit 3600
"""

import argparse
import csv
import glob
import logging
import os
import sys
import time

# WICHTIG: Hier KEINE imports von helper_functions oder anderen Modulen,
# die torch laden. Wir importieren nur was CP-SAT wirklich braucht.
from data.data_parsers import parser_fjsp
from scheduling_environment.jobShop import JobShop
from solution_methods.cp_sat.models import FJSPmodel
from solution_methods.cp_sat.utils import solve_model

logging.basicConfig(level=logging.INFO)

SIZES = ['20x10', '50x10', '100x10', '200x10', '1005', '1510', '2005']

# Diese Groessen liegen direkt unter data/fjsp/{size}/, ohne "sagc_" Praefix.
NO_PREFIX_SIZES = {'1005', '1510', '2005'}


def get_instances(size):
    subdir = size if size in NO_PREFIX_SIZES else f'sagc_{size}'
    pattern = os.path.join('data', 'fjsp', subdir, '*.fjs')
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No .fjs files found matching {pattern}")
    return files


def build_instance_path(filepath):
    """Convert absolute filepath to repo-relative path with /fjsp/ prefix for the parser."""
    data_dir = os.path.join(os.getcwd(), 'data')
    rel = os.path.relpath(filepath, data_dir).replace('\\', '/')
    return '/' + rel


def load_job_shop_env(problem_instance):
    """Minimaler Loader ohne torch."""
    jobShopEnv = JobShop()
    jobShopEnv = parser_fjsp.parse_fjsp(jobShopEnv, problem_instance, from_absolute_path=False)
    jobShopEnv._name = problem_instance
    return jobShopEnv


def run_cpsat(filepath, time_limit):
    instance_path = build_instance_path(filepath)
    jobShopEnv = load_job_shop_env(instance_path)

    model, vars = FJSPmodel.fjsp_cp_sat_model(jobShopEnv)
    solver, status, solution_count = solve_model(model, time_limit)
    jobShopEnv, results = FJSPmodel.update_env(
        jobShopEnv, vars, solver, status, solution_count, time_limit
    )

    if results:
        return {
            'makespan': results.get('objValue', -1),
            'status': results.get('statusString', 'UNKNOWN'),
            'lower_bound': results.get('lowerBound', -1),
        }
    return {'makespan': -1, 'status': 'NO_SOLUTION', 'lower_bound': -1}


def write_result(per_instance_dir, instance_name, row):
    """Schreibt eine einzelne CSV-Datei pro Instanz. Keine race conditions moeglich."""
    os.makedirs(per_instance_dir, exist_ok=True)
    csv_path = os.path.join(per_instance_dir, f'{instance_name}.csv')
    header = ['instance_name', 'makespan', 'runtime_seconds', 'status', 'lower_bound']
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description='Run CP-SAT on a single FJSSP instance')
    parser.add_argument('--size', required=True, choices=SIZES)
    parser.add_argument('--instance_idx', type=int, required=True)
    parser.add_argument('--time_limit', type=int, default=3600)
    parser.add_argument('--output_dir', type=str, default='results')
    args = parser.parse_args()

    instances = get_instances(args.size)
    if args.instance_idx < 0 or args.instance_idx >= len(instances):
        logging.error(f"instance_idx {args.instance_idx} out of range [0, {len(instances)-1}]")
        sys.exit(1)

    filepath = instances[args.instance_idx]
    instance_name = os.path.basename(filepath)
    per_instance_dir = os.path.join(args.output_dir, 'CP_SAT', args.size, 'per_instance')
    result_file = os.path.join(per_instance_dir, f'{instance_name}.csv')

    # Resumable: skip wenn Resultat schon existiert
    if os.path.exists(result_file):
        print(f"CP_SAT | {args.size} | {instance_name} | already done, skipping")
        return

    try:
        t0 = time.time()
        result = run_cpsat(filepath, args.time_limit)
        runtime = time.time() - t0
        row = [
            instance_name,
            result['makespan'],
            f'{runtime:.1f}',
            result['status'],
            result['lower_bound'],
        ]
        print(f"CP_SAT | {args.size} | {instance_name} | makespan={result['makespan']} | "
              f"status={result['status']} | time={runtime:.1f}s")
    except Exception as e:
        logging.error(f"Failed on {instance_name}: {e}")
        row = [instance_name, -1, '0.0', 'ERROR', -1]
        print(f"CP_SAT | {args.size} | {instance_name} | FAILED: {e}")

    write_result(per_instance_dir, instance_name, row)


if __name__ == '__main__':
    main()