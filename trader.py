"""Realtime Trader"""

import copy
import datetime
import sched
import time
from typing import List

from absl import app
from absl import flags

import algorithm
import feature_manager
import trading_manager

FLAGS = flags.FLAGS
flags.DEFINE_integer('frequency', 60 * 60 * 24, 'Iterating frequency (in sec)')


def _trading_sell_handler(context, trader, trading):
    transactions = trader.sell(trading)
    remained_stocks = copy.deepcopy(context.basket)
    returned_budget = 0

    for trans in transactions:
        remaining_sold_amount = trans.amount
        updated_basket = []
        for owned_stock in remained_stocks:
            # Stock code is not matched
            if owned_stock.code != trans.code:
                updated_basket.append(owned_stock)
                continue
            # Stock is more than sold amount
            if owned_stock.amount > trans.amount:
                returned_budget += trans.sold_price * trans.amount
                owned_stock.update_amount(owned_stock.amount - trans.amount)
                updated_basket.append(owned_stock)
                break
            # Sold all amount of stock
            remaining_sold_amount -= trans.amount
            returned_budget += trans.sold_price * owned_stock.amount
            if remaining_sold_amount <= 0:
                break
        remained_stocks = updated_basket

    context.update_budget(context.budget + returned_budget)
    context.update_basket(remained_stocks)

    return transactions  # to save all transactions in simulator


def _handler(trade_algorithm: algorithm.Algorithm, context: algorithm.Context,
             trader: trading_manager.TradingManager,
             features: feature_manager.FeatureManager,
             history: List[trading_manager.Transaction]):
    now = datetime.datetime.now()
    if now.isoweekday() > 5:  # if weeken,
        return

    context.update_market_time(now)
    trading_target = trade_algorithm.run(context, features)
    for trading in trading_target:
        if trading.action == 'buy':
            stock = trader.buy(trading)
            context.buy_stocks([stock])
            # TODO(jseo): append buy history to history buffer
        else:
            history.append(_trading_sell_handler(context, trader, trading))


def main(args):
    del args  # Unused

    context = algorithm.Context(budget=FLAGS.budget, basket=[])
    trade_algorithm = algorithm.DummyAlgorithm()

    trader = trading_manager.get_trading_manager('daishin')
    features = feature_manager.FeatureManager()

    # TODO(jseo): Seperate scheduler as class to manage frequency
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(FLAGS.frequency, 1, _handler,
                    (trade_algorithm, context, trader, features))
    scheduler.run(blocking=True)


if __name__ == '__main__':
    app.run(main)
