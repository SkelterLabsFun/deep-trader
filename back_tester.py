"""Back Tester"""

import copy
import datetime

from absl import app
from absl import flags
from absl import logging
import tqdm

import algorithm
import trading_manager

FLAGS = flags.FLAGS
# FLAGS for back test.
flags.DEFINE_string('start_date', '2000-01-01', 'Start date for back test.')
flags.DEFINE_string('end_date', '2020-12-31', 'End date for back test.')
flags.DEFINE_integer('budget', 10_000_000, 'Budget for back test.')

flags.DEFINE_integer('frequency', 60 * 60 * 24, 'Iterating frequency (in sec)')

ENV = 'back_test'

def algorithm_handler(trade_algorithm: algorithm.Algorithm,
             context: algorithm.Context,
             trader: trading_manager.TradingManager,
             feature_manager):
    transaction_history = []
    trading_target = trade_algorithm.run(context, feature_manager)
    # print(trading_target)
    for trading in trading_target:
        if trading.action == 'buy':
            trading_buy_handler(context, trader, trading)
        else:
            transaction_history += trading_sell_handler(
                context, trader, trading)
    return transaction_history

def trading_buy_handler(context, trader, trading):
    stock = trader.buy(trading)
    context.buy_stocks([stock])

def trading_sell_handler(context, trader, trading):
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

    return transactions # to save all transactions in simulator

def _parse_datetime(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%d')

def _date_range_enumerator(start_date, end_date, tick):
    ticks = []
    while start_date <= end_date:
        ticks.append(start_date)
        start_date += tick
    return ticks[:100]

def simulate(start_date, end_date, frequency, trade_algorithm, context, trader,
             feature_manager):
    start_date = _parse_datetime(start_date)
    end_date = _parse_datetime(end_date)
    tick = datetime.timedelta(seconds=frequency)
    print(f'Simulation date range: {start_date} ~ {end_date}')
    
    now = start_date
    transaction_history = []
    for now in tqdm.tqdm(_date_range_enumerator(start_date, end_date, tick)):
        context.update_market_time(now)
        trader.set_user_and_stock_data(context, None)
        transaction_history += algorithm_handler(
            trade_algorithm, context, trader, feature_manager)
        # print(context)
    print(transaction_history)


def main(args):
    del args  # Unused

    context = algorithm.Context(budget=FLAGS.budget, basket=[])
    trade_algorithm = algorithm.DummyAlgorithm()

    trader = trading_manager.get_trading_manager('back_test')
    feature_manager = None # feature_manager.FeatureManager()

    simulate(FLAGS.start_date, FLAGS.end_date, FLAGS.frequency, trade_algorithm,
             context, trader, feature_manager)


if __name__ == '__main__':
    app.run(main)
