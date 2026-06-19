"""
test_pipeline.py

Tests the baseline evaluation pipeline on a single instance per method.
Run locally first, then on the cluster.

Usage:
    python test_pipeline.py                    # run all methods
    python test_pipeline.py --method CP_SAT    # run only one method
    python test_pipeline.py --size 20x10       # use a different size

Requirements:
    - Run from the repo root of Job_Shop_Scheduling_Benchmark_Environments_and_Instances
    - data/fjsp/sagc_20x10/ must exist and contain at least one .fjs file
"""

import argparse
import sys
import time
import os
from pathlib import Path

# Headless matplotlib before any other imports
import matplotlib
matplotlib.use('Agg')

# ---------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--method', type=str, default=None,
                    help='Test only this method: FIFO, SPT, MOR, MWR, CP_SAT, GA')
parser.add_argument('--size', type=str, default='20x10',
                    help='Instance size folder to use, e.g. 20x10')
parser.add_argument('--time_limit', type=int, default=30,
                    help='Time limit in seconds for CP_SAT and GA (default: 30 for testing)')
args = parser.parse_args()

# ---------------------------------------------------------------
# Find test instance
# ---------------------------------------------------------------
data_dir = Path('data/fjsp') / f'sagc_{args.size}'
if not data_dir.exists():
    print(f"ERROR: Directory not found: {data_dir}")
    print("Make sure you are running from the repo root and the data folder exists.")
    sys.exit(1)

fjs_files = sorted(data_dir.glob('*.fjs'))
if not fjs_files:
    print(f"ERROR: No .fjs files found in {data_dir}")
    sys.exit(1)

test_file = fjs_files[0]
print(f"Using test instance: {test_file}")
print(f"Time limit for CP_SAT and GA: {args.time_limit}s")
print()

# The instance path as Reijnen's parser expects it (relative to data/, with leading slash)
instance_rel_path = f"/fjsp/sagc_{args.size}/{test_file.name}"

# ---------------------------------------------------------------
# Import solution methods
# ---------------------------------------------------------------
try:
    from solution_methods.helper_functions import load_job_shop_env
    print("OK: load_job_shop_env imported")
except ImportError as e:
    print(f"ERROR: Could not import load_job_shop_env: {e}")
    sys.exit(1)

try:
    from solution_methods.dispatching_rules.run_dispatching_rules import run_dispatching_rules
    print("OK: run_dispatching_rules imported")
except ImportError as e:
    print(f"ERROR: Could not import run_dispatching_rules: {e}")
    sys.exit(1)

try:
    from solution_methods.cp_sat.run_cp_sat import run_CP_SAT
    print("OK: run_CP_SAT imported")
except ImportError as e:
    print(f"ERROR: Could not import run_CP_SAT: {e}")
    print("  Likely cause: uppercase import bug (CP_SAT vs cp_sat). Apply Change 1 first.")
    sys.exit(1)

try:
    from solution_methods.GA.run_GA import run_GA
    from solution_methods.GA.src.initialization import initialize_run
    print("OK: run_GA and initialize_run imported")
except ImportError as e:
    print(f"ERROR: Could not import GA: {e}")
    sys.exit(1)

print()

# ---------------------------------------------------------------
# Helper: load a fresh JobShop env
# ---------------------------------------------------------------
def load_env(instance_rel_path):
    return load_job_shop_env(instance_rel_path)

# ---------------------------------------------------------------
# Helper: run one method and print result
# ---------------------------------------------------------------
def test_method(name, fn):
    print(f"--- Testing {name} ---")
    start = time.time()
    try:
        result = fn()
        elapsed = time.time() - start
        makespan, status = result
        print(f"  makespan = {makespan}")
        print(f"  status   = {status}")
        print(f"  time     = {elapsed:.1f}s")
        print(f"  PASSED")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  FAILED after {elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()
    print()

# ---------------------------------------------------------------
# Dispatching rule test helper
# ---------------------------------------------------------------
def make_dr_params(dispatching_rule, machine_assignment_rule):
    return {
        'instance': {
            'problem_instance': instance_rel_path,
            'online_arrivals': False,
            'dispatching_rule': dispatching_rule,
            'machine_assignment_rule': machine_assignment_rule,
        },
        'output': {
            'logbook': False, 'show_precedences': False,
            'show_gantt': False, 'save_gantt': False, 'save_results': False,
        }
    }

def run_dr(dispatching_rule, machine_assignment_rule):
    jobShopEnv = load_env(instance_rel_path)
    params = make_dr_params(dispatching_rule, machine_assignment_rule)
    makespan, _ = run_dispatching_rules(jobShopEnv, **params)
    return makespan, 'done'

# ---------------------------------------------------------------
# CP-SAT test helper
# ---------------------------------------------------------------
def run_cpsat():
    jobShopEnv = load_env(instance_rel_path)
    params = {
        'instance': {'problem_instance': instance_rel_path},
        'solver': {'time_limit': args.time_limit, 'model': 'fjsp'},
        'output': {
            'show_precedences': False, 'show_gantt': False,
            'save_gantt': False, 'save_results': False,
        }
    }
    results, _ = run_CP_SAT(jobShopEnv, **params)
    if results is None:
        return None, 'no_solution'
    makespan = results.get('objValue')
    status = results.get('statusString', 'unknown')
    return makespan, status

# ---------------------------------------------------------------
# GA test helper
# ---------------------------------------------------------------
def run_ga():
    jobShopEnv = load_env(instance_rel_path)
    params = {
        'instance': {'problem_instance': instance_rel_path},
        'algorithm': {
            'population_size': 10,      # small for testing
            'ngen': 100000,
            'seed': 42,
            'indpb': 0.1,
            'cr': 0.7,
            'multiprocessing': False,
            'time_limit': args.time_limit,
        },
        'output': {
            'logbook': False, 'show_precedences': False,
            'show_gantt': False, 'save_gantt': False, 'save_results': False,
        }
    }
    population, toolbox, stats, hof = initialize_run(jobShopEnv, **params)
    makespan, _ = run_GA(jobShopEnv, population, toolbox, stats, hof, **params)
    return makespan, 'done'

# ---------------------------------------------------------------
# Run the tests
# ---------------------------------------------------------------
methods_to_test = {
    'FIFO':   lambda: run_dr('FIFO', 'EET'),
    'SPT':    lambda: run_dr('SPT', 'SPT'),
    'MOR':    lambda: run_dr('MOR', 'EET'),
    'MWR':    lambda: run_dr('MWR', 'EET'),
    'CP_SAT': run_cpsat,
    'GA':     run_ga,
}

if args.method:
    if args.method not in methods_to_test:
        print(f"Unknown method: {args.method}. Choose from: {list(methods_to_test.keys())}")
        sys.exit(1)
    selected = {args.method: methods_to_test[args.method]}
else:
    selected = methods_to_test

print("=" * 50)
print("PIPELINE TEST")
print("=" * 50)
print()

passed = 0
failed = 0
for name, fn in selected.items():
    test_method(name, fn)

print("=" * 50)
print("Done. Check output above for PASSED / FAILED.")
print("Note: CP_SAT and GA use a short time limit for testing.")
print(f"      For real runs, use --time_limit 1800.")