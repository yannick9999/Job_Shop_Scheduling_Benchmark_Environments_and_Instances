import matplotlib
matplotlib.use('Agg')

import argparse
import csv
import glob
import logging
import os
import sys
import time

try:
    import fcntl
except ImportError:
    fcntl = None

from solution_methods.helper_functions import load_job_shop_env
from solution_methods.dispatching_rules.run_dispatching_rules import run_dispatching_rules
from solution_methods.cp_sat.run_cp_sat import run_CP_SAT
from solution_methods.GA.run_GA import run_GA
from solution_methods.GA.src.initialization import initialize_run

logging.basicConfig(level=logging.INFO)

DISPATCHING_METHODS = {'FIFO', 'SPT', 'MOR', 'MWR'}
ALL_METHODS = DISPATCHING_METHODS | {'CP_SAT', 'GA'}
SIZES = ['20x10', '50x10', '100x10', '200x10']


def get_instances(size):
    pattern = os.path.join('data', 'fjsp', f'sagc_{size}', '*.fjs')
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No .fjs files found matching {pattern}")
    return files


def build_instance_path(filepath):
    """Convert absolute filepath to repo-relative path with /fjsp/ prefix for the parser."""
    data_dir = os.path.join(os.getcwd(), 'data')
    rel = os.path.relpath(filepath, data_dir).replace('\\', '/')
    return '/' + rel


def build_params(method, instance_path, time_limit):
    if method in {'FIFO', 'MOR', 'MWR'}:
        return {
            'instance': {
                'problem_instance': instance_path,
                'online_arrivals': False,
                'dispatching_rule': method,
                'machine_assignment_rule': 'EET',
            },
            'output': {
                'logbook': False, 'show_precedences': False,
                'show_gantt': False, 'save_gantt': False, 'save_results': False,
            }
        }
    elif method == 'SPT':
        return {
            'instance': {
                'problem_instance': instance_path,
                'online_arrivals': False,
                'dispatching_rule': 'SPT',
                'machine_assignment_rule': 'SPT',
            },
            'output': {
                'logbook': False, 'show_precedences': False,
                'show_gantt': False, 'save_gantt': False, 'save_results': False,
            }
        }
    elif method == 'CP_SAT':
        return {
            'instance': {'problem_instance': instance_path},
            'solver': {'time_limit': time_limit, 'model': 'fjsp'},
            'output': {
                'show_precedences': False, 'show_gantt': False,
                'save_gantt': False, 'save_results': False,
            }
        }
    elif method == 'GA':
        return {
            'instance': {'problem_instance': instance_path},
            'algorithm': {
                'population_size': 100,
                'ngen': 100000,
                'seed': 42,
                'indpb': 0.1,
                'cr': 0.7,
                'multiprocessing': False,
                'time_limit': time_limit,
            },
            'output': {
                'logbook': False, 'show_precedences': False,
                'show_gantt': False, 'save_gantt': False, 'save_results': False,
            }
        }


def run_instance(method, filepath, time_limit):
    instance_path = build_instance_path(filepath)
    params = build_params(method, instance_path, time_limit)
    jobShopEnv = load_job_shop_env(instance_path)

    if method in DISPATCHING_METHODS:
        makespan, _ = run_dispatching_rules(jobShopEnv, **params)
        return {'makespan': makespan}
    elif method == 'CP_SAT':
        results, _ = run_CP_SAT(jobShopEnv, **params)
        if results:
            return {
                'makespan': results.get('objValue', -1),
                'status': results.get('statusString', 'UNKNOWN'),
                'lower_bound': results.get('lowerBound', -1),
            }
        return {'makespan': -1, 'status': 'NO_SOLUTION', 'lower_bound': -1}
    elif method == 'GA':
        population, toolbox, stats, hof = initialize_run(jobShopEnv, **params)
        makespan, _, generations_completed, _ = run_GA(
            jobShopEnv, population, toolbox, stats, hof, **params)
        return {'makespan': makespan, 'generations_completed': generations_completed}


def get_csv_header(method):
    if method in DISPATCHING_METHODS:
        return ['instance_name', 'makespan', 'runtime_seconds']
    elif method == 'CP_SAT':
        return ['instance_name', 'makespan', 'runtime_seconds', 'status', 'lower_bound']
    elif method == 'GA':
        return ['instance_name', 'makespan', 'runtime_seconds', 'generations_completed']


def append_result(csv_path, header, row):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    write_header = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='') as f:
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_EX)
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description='Run baseline methods on FJSSP instances')
    parser.add_argument('--method', required=True, choices=sorted(ALL_METHODS))
    parser.add_argument('--size', required=True, choices=SIZES)
    parser.add_argument('--instance_idx', type=int, default=None)
    parser.add_argument('--time_limit', type=int, default=1800)
    parser.add_argument('--output_dir', type=str, default='results')
    args = parser.parse_args()

    instances = get_instances(args.size)

    if args.instance_idx is not None:
        if args.instance_idx < 0 or args.instance_idx >= len(instances):
            logging.error(f"instance_idx {args.instance_idx} out of range [0, {len(instances)-1}]")
            sys.exit(1)
        instances = [instances[args.instance_idx]]

    csv_path = os.path.join(args.output_dir, args.method, f'{args.size}.csv')
    header = get_csv_header(args.method)

    for filepath in instances:
        instance_name = os.path.basename(filepath)
        try:
            t0 = time.time()
            result = run_instance(args.method, filepath, args.time_limit)
            runtime = time.time() - t0

            makespan = result['makespan']
            if args.method in DISPATCHING_METHODS:
                row = [instance_name, makespan, f'{runtime:.1f}']
            elif args.method == 'CP_SAT':
                row = [instance_name, makespan, f'{runtime:.1f}',
                       result['status'], result['lower_bound']]
            elif args.method == 'GA':
                row = [instance_name, makespan, f'{runtime:.1f}',
                       result['generations_completed']]

            print(f"{args.method} | {args.size} | {instance_name} | makespan={makespan} | time={runtime:.1f}s")

        except Exception as e:
            logging.error(f"Failed on {instance_name}: {e}")
            runtime = 0.0
            if args.method in DISPATCHING_METHODS:
                row = [instance_name, -1, f'{runtime:.1f}']
            elif args.method == 'CP_SAT':
                row = [instance_name, -1, f'{runtime:.1f}', 'ERROR', -1]
            elif args.method == 'GA':
                row = [instance_name, -1, f'{runtime:.1f}', -1]

            print(f"{args.method} | {args.size} | {instance_name} | makespan=-1 | FAILED: {e}")

        append_result(csv_path, header, row)


if __name__ == '__main__':
    main()
