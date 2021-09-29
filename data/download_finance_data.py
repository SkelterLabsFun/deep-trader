"""Download finance data using FinanceDataReader.

And save as TFRecord dataset.

@see https://github.com/FinanceData/FinanceDataReader

Example usage:

    python download_finance_data.py --outfile ~/tmp/finance_data.tfrecord
"""
import math

from absl import app
from absl import flags
from absl import logging
import FinanceDataReader as fdr
import numpy as np
import pandas as pd
import tensorflow as tf

FLAGS = flags.FLAGS
flags.DEFINE_string('outfile', None, 'Output file path to TFRecord.')


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


def _build_example(code, ohlcvc):
    """Return an ohlcvc example.

    An example consists of Open, High, Low, Close, Volume, Change and
    Date columns. Each column value is n-day list of float except date
    string.

    For an example;

    Code |Open |High |Low |Close |Volume |Change |Date
    -----|-----|-----|----|------|-------|-------|------
    Code |10   |12   |9   |10    |100    |0      |YYYY-mm-dd
    ...
    Code |15   |18   |12  |17    |220    |0.0209 |YYYY-mm-dd + ndays
    """
    feature = {
        'code': _bytes_feature([code]),
        'date': _bytes_feature(_strftime_values(ohlcvc.index)),
        'open': _float_feature(_float_values(ohlcvc['Open'])),
        'high': _float_feature(_float_values(ohlcvc['High'])),
        'low': _float_feature(_float_values(ohlcvc['Low'])),
        'close': _float_feature(_float_values(ohlcvc['Close'])),
        'volume': _float_feature(_float_values(ohlcvc['Volume'])),
        'change': _float_feature(_float_values(ohlcvc['Change'])),
    }
    return tf.train.Example(features=tf.train.Features(feature=feature))


def _download_krx(writer):
    df_krx = fdr.StockListing('KRX')
    count = 0
    for symbol, sector in zip(df_krx['Symbol'], df_krx['Sector']):

        # For example,
        # {Symbol: "58G192", Market: "KOSPI", Name: "KBG192LG화학콜"},
        # all other columns are NaNs. They have no "ohlcvc" and raise
        # `ValueError: symbol not found` from DataReader. Skip them.
        if isinstance(sector, float) and math.isnan(sector):
            logging.info(f'Skipped KRX: {symbol}')
            continue

        # Open, High, Low, Close, Volume, Change
        ohlcvc = fdr.DataReader(symbol)
        try:
            example = _build_example(symbol, ohlcvc)
            writer.write(example.SerializeToString())
            count += 1
            if count % 100 == 0:
                logging.info(f'Downloaded {count} examples')
        except KeyError as ex:
            # I saw `KeyError: 'Open' for 257720` on 2021-09-29 5 AM.
            # "실리콘2" just gets listed on exchange market at the time.
            logging.warning(f'KeyError: {ex} for {symbol}')

    if count % 100 > 0:
        logging.info(f'Downloaded {count} examples')


def main(args):
    del args  # Unused

    with tf.io.TFRecordWriter(FLAGS.outfile) as writer:
        _download_krx(writer)


if __name__ == '__main__':
    flags.mark_flags_as_required([
        'outfile',
    ])
    app.run(main)
