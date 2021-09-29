r"""Convert company data to TFRecord dataset.

Just file format conversion. Input is a crawled CSV/TSV file with
following columns:

- code
- corp_name
- year
- total_equity
- sales
- profit
- net_income
- bps
- per
- eps
- debt_ratio
- profit_ratio

Example usage:

    python convert_company_data.py \
      --infile ~/tmp/company_data.csv --outfile ~/tmp/company_data.tfrecord
"""
import math

from absl import app
from absl import flags
from absl import logging
import numpy as np
import pandas as pd
import tensorflow as tf

FLAGS = flags.FLAGS
flags.DEFINE_string('infile', None, 'Path to input CSV file.')
flags.DEFINE_string('outfile', None, 'Path to output TFRecord file.')


# TODO(jaesup): Dedup same conversion functions in `download_finance_data.py`.
def _bytes_feature(values):
    """Return an bytes_list from str list."""
    bytes_values = []
    for v in values:
        if isinstance(v, str):
            bytes_values.append(str.encode(v))
        else:
            bytes_values.append(v)
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=bytes_values))


def _int64_feature(values):
    """Returns an int64_list from a bool / enum / int / uint list."""
    return tf.train.Feature(int64_list=tf.train.Int64List(value=values))


def _float_feature(values):
    """Returns an float_list from a bool / enum / int / uint list."""
    return tf.train.Feature(float_list=tf.train.FloatList(value=values))


def _strftime_values(series):
    return pd.to_datetime(series.values).strftime('%Y-%m-%d')


def _float_values(series):
    return series.values.astype(np.float32)


def _build_example(company):
    """Return an company example.

    An example consists of company features such as total_equity,
    sale, profit and identifying columns (code, name, year). Each
    column value is 1 element list of float or string.

    For an example;

    code |name |year | ... |tot.equity |sales | ...
    -----|-----|-----|-----|-----------|------|------
    10   |gana |2009 |     |100        |10.0  |
    ...                ...                      ...
    15   |hong | 12  |     |220        |700.0 |
    """
    feature = {
        'code': _bytes_feature([company.code]),
        'corp_name': _bytes_feature([company.corp_name]),
        'year': _float_feature([company.year]),
        'total_equity': _float_feature([company.total_equity]),
        'sales': _float_feature([company.sales]),
        'profit': _float_feature([company.profit]),
        'net_income': _float_feature([company.net_income]),
        'bps': _float_feature([company.bps]),
        'per': _float_feature([company.per]),
        'eps': _float_feature([company.eps]),
        'debt_ratio': _float_feature([company.debt_ratio]),
        'profit_ratio': _float_feature([company.profit_ratio]),
    }
    return tf.train.Example(features=tf.train.Features(feature=feature))


def _convert_company_data(writer):
    df_company = pd.read_csv(
        FLAGS.infile,
        sep='\t',
        dtype={
            'code': str,
            'corp_name': str,
            'year': np.float32,
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
    count = 0
    for company in df_company.itertuples():
        example = _build_example(company)
        writer.write(example.SerializeToString())
        count += 1
        if count % 100 == 0:
            logging.info(f'Converted {count} examples')

    if count % 100 > 0:
        logging.info(f'Converted {count} examples')


def main(args):
    del args  # Unused

    with tf.io.TFRecordWriter(FLAGS.outfile) as writer:
        _convert_company_data(writer)


if __name__ == '__main__':
    flags.mark_flags_as_required([
        'infile',
        'outfile',
    ])
    app.run(main)
