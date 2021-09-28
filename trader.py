"""Realtime Trader"""

import sched
import time

from absl import app
from absl import flags

from experimental.demodays2021.deep_traders import algorithm

FLAGS = flags.FLAGS
flags.DEFINE_integer('frequency', 60 * 60 * 24, 'Iterating frequency (in sec)')


def _handler(trade_algorithm: algorithm.Algorithm,
             trader: trading_manager.TradingManager,
             features: feature_manager.FeatureManager):
    trading_target = trade_algorithm.run(features)
    for trading in trading_target:
        if trading.action == 'buy':
            trader.buy(trading)
        else:
            trader.sell(trading)


def main(args):
    del args  # Unused

    trade_algorithm = algorithm.Algorithm()

    trader = trading_manager.TradingManager()
    features = feature_manager.FeatureManager()

    # TODO(jseo): Seperate scheduler as class to manage frequency
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(FLAGS.frequency, 1, _handler,
                    (trade_algorithm, trader, features))
    scheduler.run(blocking=True)


if __name__ == '__main__':
    app.run(main)
