import matplotlib
matplotlib.use('Agg')

import argparse
import csv
import glob
import logging
import os
import time

from solution_methods.helper_functions import load_job_shop_env
from solution_methods.GA.run_GA import run_GA
from solution_methods.GA.src.initialization import initialize_run

logging.basicConfig(level=logging.INFO)

SIZES = ['20x10', '50x10', '100x10', '200x10']
HEADER = ['instance_name', 'makespan', 'runtime_seconds', 'generations_completed']

# Smaller population for large instances so more generations fit in the time budget.
# Parallelism comes from running 5 jobs simultaneously (submit_ga_split.sh),
# not from multiprocessing within a single GA run.
POPULATION_CONFIG = {
    '20x10':  {'population_size': 100},
    '50x10':  {'population_size':  50},
    '100x10': {'population_size':  30},
    '200x10': {'population_size':  20},
}


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


def build_params(instance_path, size, time_limit, use_multiprocessing):
    cfg = POPULATION_CONFIG[size]
    return {
        'instance': {'problem_instance': instance_path},
        'algorithm': {
            'population_size': cfg['population_size'],
            'ngen': 100000,
            'seed': 42,
            'indpb': 0.1,
            'cr': 0.7,
            'multiprocessing': use_multiprocessing,
            'time_limit': time_limit,
        },
        'output': {
            'logbook': False, 'show_precedences': False,
            'show_gantt': False, 'save_gantt': False, 'save_results': False,
        }
    }


def run_instance(filepath, size, time_limit, use_multiprocessing):
    instance_path = build_instance_path(filepath)
    params = build_params(instance_path, size, time_limit, use_multiprocessing)
    jobShopEnv = load_job_shop_env(instance_path)
    population, toolbox, stats, hof = initialize_run(jobShopEnv, **params)
    makespan, _, generations_completed, _ = run_GA(
        jobShopEnv, population, toolbox, stats, hof, **params)
    return makespan, generations_completed


def write_row(csv_path, row):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(HEADER)
        writer.writerow(row)
        f.flush()
        os.fsync(f.fileno())


def main():
    parser = argparse.ArgumentParser(description='Run GA on FJSSP instances')
    parser.add_argument('--size', required=True, choices=SIZES)
    parser.add_argument('--start_idx', type=int, default=0)
    parser.add_argument('--end_idx', type=int, default=99)
    parser.add_argument('--time_limit', type=int, default=3600)
    parser.add_argument('--output_dir', type=str, default='results')
    parser.add_argument('--multiprocessing', action='store_true',
                        help='Enable multiprocessing for fitness evaluation (experimental, may cause crashes)')
    args = parser.parse_args()

    use_multiprocessing = args.multiprocessing
    cfg = POPULATION_CONFIG[args.size]

    logging.info(
        f"GA config for {args.size}: population={cfg['population_size']}, "
        f"multiprocessing={use_multiprocessing}, "
        f"time_limit={args.time_limit}s, "
        f"instances={args.start_idx}-{args.end_idx}"
    )

    all_instances = get_instances(args.size)
    instances = all_instances[args.start_idx:args.end_idx + 1]

    if not instances:
        logging.error(f"No instances in range [{args.start_idx}, {args.end_idx}]")
        return

    csv_path = os.path.join(args.output_dir, 'GA', f'{args.size}.csv')

    # Resume logic: read already completed instances from CSV.
    # Only successful runs are recorded, so failed instances will be retried.
    done = set()
    if os.path.isfile(csv_path):
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                done.add(row['instance_name'])
        logging.info(f"Resuming: {len(done)} instances already done for GA {args.size}")

    for filepath in instances:
        instance_name = os.path.basename(filepath)
        if instance_name in done:
            continue

        try:
            t0 = time.time()
            makespan, generations = run_instance(
                filepath, args.size, args.time_limit, use_multiprocessing)
            runtime = time.time() - t0

            # Sanity check: only write valid results to CSV.
            if makespan is None or makespan <= 0:
                logging.error(
                    f"Invalid makespan ({makespan}) for {instance_name}, NOT writing to CSV"
                )
                print(f"GA | {args.size} | {instance_name} | INVALID RESULT, will retry next run")
                continue

            row = [instance_name, makespan, f'{runtime:.1f}', generations]
            write_row(csv_path, row)
            print(
                f"GA | {args.size} | {instance_name} | makespan={makespan} | "
                f"generations={generations} | time={runtime:.1f}s"
            )

        except Exception as e:
            # Do NOT write failed instances to CSV. They will be retried on next run.
            logging.error(f"Failed on {instance_name}: {e}")
            print(f"GA | {args.size} | {instance_name} | FAILED, will retry next run: {e}")


if __name__ == '__main__':
    main()