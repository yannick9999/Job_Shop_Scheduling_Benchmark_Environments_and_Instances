"""
Find missing instance indices for CP-SAT runs.

Compares the list of .fjs files in data/fjsp/sagc_{size}/ with the
instance names recorded in results/CP_SAT/{size}/per_instance/*.csv files.

Prints the missing indices (0-based) as a space-separated list to stdout,
which can be consumed directly by run_cpsat_missing.sh.

Usage:
    python find_missing.py --size 20x10
    # Output: 17 29 42 45
"""

import argparse
import csv
import glob
import os
import sys


# Diese Groessen liegen direkt unter data/fjsp/{size}/, ohne "sagc_" Praefix.
NO_PREFIX_SIZES = {'1005', '1510', '2005'}

SIZES = ['20x10', '50x10', '100x10', '200x10', '1005', '1510', '2005']


def find_missing(size):
    subdir = size if size in NO_PREFIX_SIZES else f'sagc_{size}'
    pattern = os.path.join('data', 'fjsp', subdir, '*.fjs')
    all_files = sorted(glob.glob(pattern))
    if not all_files:
        print(f"ERROR: No .fjs files found matching {pattern}", file=sys.stderr)
        sys.exit(1)

    all_names = [os.path.basename(f) for f in all_files]

    # Read all per-instance CSVs and collect the instance names that completed.
    done = set()
    csv_dir = os.path.join('results', 'CP_SAT', size, 'per_instance')
    if os.path.isdir(csv_dir):
        for csv_file in glob.glob(os.path.join(csv_dir, '*.csv')):
            try:
                with open(csv_file, newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get('instance_name')
                        if name:
                            done.add(name)
            except Exception as e:
                print(f"WARN: Could not read {csv_file}: {e}", file=sys.stderr)

    missing_indices = [i for i, name in enumerate(all_names) if name not in done]
    return all_names, done, missing_indices


def main():
    parser = argparse.ArgumentParser(description='Find missing CP-SAT instance indices')
    parser.add_argument('--size', required=True, choices=SIZES)
    parser.add_argument('--verbose', action='store_true',
                        help='Print summary to stderr instead of just indices')
    args = parser.parse_args()

    all_names, done, missing = find_missing(args.size)

    if args.verbose:
        print(f"Total instances: {len(all_names)}", file=sys.stderr)
        print(f"Completed: {len(done)}", file=sys.stderr)
        print(f"Missing: {len(missing)}", file=sys.stderr)
        for idx in missing:
            print(f"  index {idx}: {all_names[idx]}", file=sys.stderr)

    # Print indices on stdout for consumption by the Slurm script.
    print(' '.join(str(i) for i in missing))


if __name__ == '__main__':
    main()