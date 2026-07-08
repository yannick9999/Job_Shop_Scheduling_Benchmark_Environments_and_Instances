"""Compare the dispatching rules FIFO, MOR, MWR, SPT across instance sizes.

For each instance size, computes the average makespan per dispatching rule,
plus a "best of 4 DR" column: for every instance the best (lowest) makespan
among the four rules is selected, and those per-instance bests are averaged.

Reads per-instance results from results/<RULE>/<size>.csv and writes:
  - results/song_dr.xlsx (Excel workbook with the resulting table)
"""
import os

import pandas as pd

RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))
DISPATCHING_RULES = ['FIFO', 'MOR', 'MWR', 'SPT']
INSTANCE_SIZES = ['1005', '2005', '1510', '2010', '3010', '4010']


def load_makespans(rule, size):
    path = os.path.join(RESULTS_DIR, rule, f'{size}.csv')
    df = pd.read_csv(path)
    return df.set_index('instance_name')['makespan']


def build_table():
    rows = []
    for size in INSTANCE_SIZES:
        per_rule = {rule: load_makespans(rule, size) for rule in DISPATCHING_RULES}
        combined = pd.DataFrame(per_rule)

        row = {'instance_size': size}
        for rule in DISPATCHING_RULES:
            row[rule] = combined[rule].mean()
        row['best_of_4_DR'] = combined.min(axis=1).mean()
        rows.append(row)

    return pd.DataFrame(rows, columns=['instance_size'] + DISPATCHING_RULES + ['best_of_4_DR'])


def main():
    table = build_table()

    xlsx_path = os.path.join(RESULTS_DIR, 'song_dr.xlsx')
    table.to_excel(xlsx_path, index=False, sheet_name='song_dr')

    print(table.to_string(index=False))


if __name__ == '__main__':
    main()
