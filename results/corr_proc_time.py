"""Correlation between the processing time of an operation and the
processing time of the next operation in the same job.

For each dataset, every job contributes one (proc_time[i], proc_time[i+1])
pair per pair of consecutive operations. An operation's processing time is
the mean duration across its eligible machines. All pairs from all
instances in a dataset are pooled and the Pearson correlation coefficient
is computed, giving one value per dataset.

Reads instances from data/fjsp/hurink/{edata,vdata,rdata},
data/fjsp/{1005,2005,1510,2010,3010,4010} and data/fjsp/brandimarte, and writes:
  - results/corr_proc_time.xlsx (Excel workbook with the resulting table)
"""
import os
import re

import pandas as pd

RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(RESULTS_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data', 'fjsp')

HURINK_DATASETS = ['edata', 'vdata', 'rdata']
SONG_DATASETS = ['1005', '2005', '1510', '2010', '3010', '4010']
BRANDIMARTE_DATASETS = ['brandimarte']


def dataset_folder(name):
    if name in HURINK_DATASETS:
        return os.path.join(DATA_DIR, 'hurink', name)
    return os.path.join(DATA_DIR, name)


def parse_operation_times(path):
    """Return a list of jobs, each a list of mean processing times per operation."""
    with open(path) as f:
        lines = [line for line in f if line.strip()]

    num_jobs = int(float(re.findall(r'\S+', lines[0])[0]))

    jobs = []
    for line in lines[1:1 + num_jobs]:
        tokens = [int(float(t)) for t in re.findall(r'\S+', line)]
        idx = 1
        op_times = []
        while idx < len(tokens):
            num_options = tokens[idx]
            durations = tokens[idx + 2: idx + 2 + 2 * num_options: 2]
            op_times.append(sum(durations) / num_options)
            idx += 1 + 2 * num_options
        jobs.append(op_times)
    return jobs


def collect_consecutive_pairs(folder):
    current, nxt = [], []
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith('.fjs'):
            continue
        for op_times in parse_operation_times(os.path.join(folder, filename)):
            current.extend(op_times[:-1])
            nxt.extend(op_times[1:])
    return current, nxt


def dataset_correlation(name):
    current, nxt = collect_consecutive_pairs(dataset_folder(name))
    return pd.Series(current).corr(pd.Series(nxt))


def build_table():
    rows = [{'dataset': name, 'correlation': dataset_correlation(name)}
            for name in HURINK_DATASETS + SONG_DATASETS + BRANDIMARTE_DATASETS]
    table = pd.DataFrame(rows, columns=['dataset', 'correlation'])

    hurink_avg = table[table['dataset'].isin(HURINK_DATASETS)]['correlation'].mean()
    song_avg = table[table['dataset'].isin(SONG_DATASETS)]['correlation'].mean()
    brandimarte_avg = table[table['dataset'].isin(BRANDIMARTE_DATASETS)]['correlation'].mean()
    table.loc[len(table)] = ['average hurink', hurink_avg]
    table.loc[len(table)] = ['average song', song_avg]
    table.loc[len(table)] = ['average brandimarte', brandimarte_avg]

    return table


def main():
    table = build_table()

    xlsx_path = os.path.join(RESULTS_DIR, 'corr_proc_time.xlsx')
    table.to_excel(xlsx_path, index=False, sheet_name='corr_proc_time')

    print(table.to_string(index=False))


if __name__ == '__main__':
    main()
