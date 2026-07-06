import matplotlib
matplotlib.use('Agg')

import argparse
import csv
import glob
import logging
import os
import sys
import time

from solution_methods.helper_functions import load_job_shop_env
from solution_methods.dispatching_rules.run_dispatching_rules import run_dispatching_rules

logging.basicConfig(level=logging.INFO)

DISPATCHING_METHODS = ['FIFO', 'SPT', 'MOR', 'MWR']
SIZES = ['edata', 'rdata', 'vdata']
HEADER = ['instance_name', 'makespan', 'runtime_seconds']


def get_instances(size):
    pattern = os.path.join('data', 'fjsp', size, '*.fjs')
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No .fjs files found matching {pattern}")
    return files


def build_instance_path(filepath):
    data_dir = os.path.join(os.getcwd(), 'data')
    rel = os.path.relpath(filepath, data_dir).replace('\\', '/')
    return '/' + rel


def build_params(method, instance_path):
    base = {
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
    if method == 'SPT':
        base['instance']['machine_assignment_rule'] = 'SPT'
    return base


def run_instance(method, filepath):
    instance_path = build_instance_path(filepath)
    params = build_params(method, instance_path)
    jobShopEnv = load_job_shop_env(instance_path)
    makespan, _ = run_dispatching_rules(jobShopEnv, **params)
    return makespan


def write_row(csv_path, row):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(HEADER)
        writer.writerow(row)


def format_duration(seconds):
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f'{hours}h{minutes:02d}m'
    if minutes:
        return f'{minutes}m{secs:02d}s'
    return f'{secs}s'


def run_size_for_method(method, size, output_dir, elapsed_so_far, total_remaining):
    instances = get_instances(size)
    csv_path = os.path.join(output_dir, 'DR', method, f'{size}.csv')

    # Skip already completed instances (resumable)
    done = set()
    if os.path.isfile(csv_path):
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                done.add(row['instance_name'])
        logging.info(f"Resuming: {len(done)} instances already done for {method} {size}")

    for filepath in instances:
        instance_name = os.path.basename(filepath)
        if instance_name in done:
            total_remaining[0] -= 1
            continue
        try:
            t0 = time.time()
            makespan = run_instance(method, filepath)
            runtime = time.time() - t0
            row = [instance_name, makespan, f'{runtime:.1f}']
            status = f"makespan={makespan} | time={runtime:.1f}s"
        except Exception as e:
            logging.error(f"Failed on {instance_name}: {e}")
            runtime = 0.0
            row = [instance_name, -1, '0.0']
            status = f"FAILED: {e}"

        write_row(csv_path, row)

        elapsed_so_far[0] += runtime
        total_remaining[0] -= 1
        done_count = elapsed_so_far[1]
        done_count += 1
        elapsed_so_far[1] = done_count
        avg = elapsed_so_far[0] / done_count if done_count else 0
        eta = format_duration(avg * total_remaining[0])
        print(f"{method} | {size} | {instance_name} | {status} | ETA={eta}")


def main():
    parser = argparse.ArgumentParser(description='Run dispatching rules on FJSSP instances')
    parser.add_argument('--method', required=True, choices=DISPATCHING_METHODS + ['all'])
    parser.add_argument('--size', required=True, choices=SIZES + ['all'], nargs='+')
    parser.add_argument('--output_dir', type=str, default='results')
    args = parser.parse_args()

    methods = DISPATCHING_METHODS if args.method == 'all' else [args.method]
    if 'all' in args.size:
        sizes = SIZES
    else:
        sizes = args.size

    # total instance count across all (method, size) combos, for the ETA
    total_remaining = [sum(len(get_instances(size)) for size in sizes) * len(methods)]
    elapsed_so_far = [0.0, 0]  # [total runtime spent, instances timed]

    for method in methods:
        for size in sizes:
            run_size_for_method(method, size, args.output_dir, elapsed_so_far, total_remaining)


if __name__ == '__main__':
    main()