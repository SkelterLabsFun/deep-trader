"""Company fundamental table.

The table lookup by company code and year to result a row consisting
of:

- code
- year
- corp_name
- total_equity
- sales
- profit
- net_income
- bps
- per
- eps
- debt_ratio
- profit_ratio

NOTE: The table should be updated once a year at least. Check and warn
if it seems not?
"""

import numpy as np
import pandas as pd
import tensorflow as tf


def load(filepath):
    """Returns dict of StaticHashTable's company fundamental data loaded.

    NOTE: Do not forget to run initializers if used in tensorflow
    graph mode.
    """
    # TODO(jaesup): Dedup with `convert_company_data.py`.
    df_company = pd.read_csv(
        filepath,
        sep='\t',
        dtype={
            'code': str,
            'year': str,
            'corp_name': str,
            'total_equity': np.float32,
            'sales': np.float32,
            'profit': np.float32,
            'net_income': np.float32,
            'bps': np.float32,
            'per': np.float32,
            'eps': np.float32,
            'debt_ratio': np.float32,
            'profit_ratio': np.float32,
        })

    tables = {}

    # Key tensor is common among all lookup tables.
    keys_t = tf.constant(df_company['code'] + '@' + df_company['year'])

    # Company name lookup table value dtype is tf.string.
    vals_t = tf.constant(df_company['corp_name'])
    initializer = tf.lookup.KeyValueTensorInitializer(keys_t, vals_t)
    tables['corp_name'] = tf.lookup.StaticHashTable(
        initializer, default_value='')

    # Other lookup tables, dtype is tf.float32.
    for colname in [
            'total_equity',
            'sales',
            'profit',
            'net_income',
            'bps',
            'per',
            'eps',
            'debt_ratio',
            'profit_ratio',
    ]:
        vals_t = tf.constant(df_company[colname])
        initializer = tf.lookup.KeyValueTensorInitializer(keys_t, vals_t)
        tables[colname] = tf.lookup.StaticHashTable(
            initializer, default_value=0)  # TODO(jaesup): Is OK default 0?

    return tables


def _test(filepath):
    tables = load(filepath)
    print('lookup corp_name:',
          tables['corp_name'].lookup(tf.constant(['', '017960@2020'])))
    print('lookup per:', tables['per'].lookup(tf.constant(['', '017960@2020'])))
    print('lookup profit_ratio:',
          tables['profit_ratio'].lookup(tf.constant(['', '017960@2020'])))


if __name__ == '__main__':
    _test('/nas0/home/jaesup.kwak/deep_traders/financial_data.txt')
