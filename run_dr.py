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
SIZES = ['20x10', '50x10', '100x10', '200x10']
HEADER = ['instance_name', 'makespan', 'runtime_seconds']


def get_instances(size):
    pattern = os.path.join('data', 'fjsp', f'sagc_{size}', '*.fjs')
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


def main():
    parser = argparse.ArgumentParser(description='Run dispatching rules on FJSSP instances')
    parser.add_argument('--method', required=True, choices=DISPATCHING_METHODS)
    parser.add_argument('--size', required=True, choices=SIZES)
    parser.add_argument('--output_dir', type=str, default='results')
    args = parser.parse_args()

    instances = get_instances(args.size)
    csv_path = os.path.join(args.output_dir, 'DR', args.method, f'{args.size}.csv')

    # Skip already completed instances (resumable)
    done = set()
    if os.path.isfile(csv_path):
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                done.add(row['instance_name'])
        logging.info(f"Resuming: {len(done)} instances already done for {args.method} {args.size}")

    for filepath in instances:
        instance_name = os.path.basename(filepath)
        if instance_name in done:
            continue
        try:
            t0 = time.time()
            makespan = run_instance(args.method, filepath)
            runtime = time.time() - t0
            row = [instance_name, makespan, f'{runtime:.1f}']
            print(f"{args.method} | {args.size} | {instance_name} | makespan={makespan} | time={runtime:.1f}s")
        except Exception as e:
            logging.error(f"Failed on {instance_name}: {e}")
            row = [instance_name, -1, '0.0']
            print(f"{args.method} | {args.size} | {instance_name} | FAILED: {e}")

        write_row(csv_path, row)


if __name__ == '__main__':
    main()