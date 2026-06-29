import matplotlib
matplotlib.use('Agg')

import csv
import glob
import logging
import os
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

DISPATCHING_METHODS = {'FIFO'}
ALL_METHODS = DISPATCHING_METHODS
SIZES = ['300x30']


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


def run_combination(method, size, output_dir):
    instances = get_instances(size)
    csv_path = os.path.join(output_dir, method, f'{size}.csv')
    header = get_csv_header(method)

    total = len(instances)
    t_start = time.time()

    for i, filepath in enumerate(instances, 1):
        instance_name = os.path.basename(filepath)
        try:
            t0 = time.time()
            result = run_instance(method, filepath, time_limit=1800)
            runtime = time.time() - t0

            makespan = result['makespan']
            if method in DISPATCHING_METHODS:
                row = [instance_name, makespan, f'{runtime:.1f}']
            elif method == 'CP_SAT':
                row = [instance_name, makespan, f'{runtime:.1f}',
                       result['status'], result['lower_bound']]
            elif method == 'GA':
                row = [instance_name, makespan, f'{runtime:.1f}',
                       result['generations_completed']]

        except Exception as e:
            logging.error(f"Failed on {instance_name}: {e}")
            runtime = 0.0
            makespan = -1
            if method in DISPATCHING_METHODS:
                row = [instance_name, -1, f'{runtime:.1f}']
            elif method == 'CP_SAT':
                row = [instance_name, -1, f'{runtime:.1f}', 'ERROR', -1]
            elif method == 'GA':
                row = [instance_name, -1, f'{runtime:.1f}', -1]

        elapsed = time.time() - t_start
        avg_per_instance = elapsed / i
        eta = avg_per_instance * (total - i)
        eta_min, eta_sec = divmod(int(eta), 60)
        print(f"[{i}/{total}] {method} | {size} | {instance_name} | makespan={makespan} | time={runtime:.1f}s | ETA: {eta_min}m {eta_sec}s")

        append_result(csv_path, header, row)

    total_elapsed = time.time() - t_start
    print(f"Done {method} | {size}: {total} instances in {total_elapsed:.1f}s\n")


def main():
    methods = sorted(ALL_METHODS)
    combos = [(m, s) for m in methods for s in SIZES]
    total_combos = len(combos)

    print(f"Running {total_combos} combinations: {len(methods)} methods x {len(SIZES)} sizes\n")

    t_global = time.time()
    for idx, (method, size) in enumerate(combos, 1):
        print(f"=== [{idx}/{total_combos}] {method} / {size} ===")
        run_combination(method, size, output_dir='results')

    total_time = time.time() - t_global
    t_min, t_sec = divmod(int(total_time), 60)
    print(f"All done. Total time: {t_min}m {t_sec}s")


if __name__ == '__main__':
    main()
