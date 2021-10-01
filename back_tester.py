"""Back Tester"""

import copy
import datetime

from absl import app
from absl import flags
from absl import logging
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from pykrx import stock as krx_stock
import tqdm

import FinanceDataReader as fdr

import algorithm
import feature_manager as feature_manager_helper
import multi_factor_market_timing
import trading_manager

matplotlib.use('macosx')

FLAGS = flags.FLAGS
# FLAGS for back test.
flags.DEFINE_string('start_date', '2001-01-03', 'Start date for back test.')
#flags.DEFINE_string('start_date', '2001-01-02', 'Start date for back test.')
flags.DEFINE_string('end_date', '2020-12-31', 'End date for back test.')
flags.DEFINE_integer('budget', 10_000_000, 'Budget for back test.')

ENV = 'back_test'

logging.debug = logging.info


def _diff_percentage(hypo, ref):
    return round((hypo - ref) / ref * 100, 3)


class MetricManager:
    """Metric Manager to calculate and print results of back test."""

    def __init__(self, budget, feature_manager):
        self._init_budget = budget
        self._feature_manager = feature_manager
        # private variable to calculate MDD(Max DrawDown)
        self._market_dates = []
        self._max_total_asset = budget
        self._mdd_list = []

        self._profit_rate = 0
        self._asset_list = []
        self._last_total_asset = budget

    def update_metric_by_context(self, context):
        if context.market_time is None:
            # Metric Manager does not support for real time trader.
            return

        current_asset = context.budget
        for owned_stock in context.basket.values():
            min_price = self._feature_manager.get_feature_at(
                owned_stock.code, 'Close', time=context.market_time)
            if min_price is None:
                return
            current_asset += int(owned_stock.amount * min_price)

        if current_asset > self._max_total_asset:
            self._max_total_asset = current_asset

        self._market_dates += [context.market_time]
        self._profit_rate = _diff_percentage(current_asset, self._init_budget)
        self._mdd_list += [
            _diff_percentage(current_asset, self._max_total_asset)
        ]
        self._asset_list += [current_asset]

    def _get_mdd(self):
        if not self._mdd_list:
            return 0
        return min(self._mdd_list)

    def _get_profit(self):
        return self._asset_list[-1] - self._init_budget

    def _get_profit_rate(self):
        return self._profit_rate

    def report(self):
        print('------------ Report for Back Test ------------')
        print(f'Profit: {self._get_profit()} ({self._get_profit_rate()}%)')
        print(f'MDD(Max Drawdown): {self._get_mdd()}%')
        # print(self._mdd_list)

    NAME_TO_CODE = {
        'KOSPI': 'KS11',
        'KOSDAQ': 'KQ11',
    }

    def plot_profit_rate(self, comparisons=None):
        comparisons = [] if comparisons is None else comparisons

        min_market_date = min(self._market_dates)
        max_market_date = max(self._market_dates)

        candidates = [('BACK_TEST',
                       np.array(self._asset_list) / self._init_budget)]
        for comparison in comparisons:
            comp_code = self.NAME_TO_CODE[comparison]
            prices = self._feature_manager.get_feature(
                comp_code, 'Close', start=min_market_date,
                end=max_market_date)[self._market_dates].values
            candidates += [(comparison, np.array(prices) / prices[0])]

        for (label, data) in candidates:
            plt.plot(self._market_dates, data, label=label)

        plt.legend()
        plt.show()


def check_delisting(context: algorithm.Context):
    date = context.market_time
    close_prices = krx_stock.get_market_ohlcv_by_ticker(
        date.strftime('%Y%m%d'), market='ALL')
    close_prices = close_prices['종가']
    valids = {}
    for stock in context.basket.values():
        if stock.code in close_prices:
            valids[stock.code] = stock
        else:
            logging.info(f'[{context.market_time}] {stock.code} is delisted.')
    context.update_basket(valids)
    return context


def algorithm_handler(trade_algorithm: algorithm.Algorithm,
                      context: algorithm.Context,
                      trader: trading_manager.TradingManager, feature_manager):
    context = check_delisting(context)
    transaction_history = []
    trading_target = trade_algorithm.run(context, feature_manager)
    logging.debug(f'[{context.market_time.strftime("%Y-%m-%d")}] '
                  f'trading result: {trading_target}')
    for trading in trading_target:
        if trading.action == 'buy':
            trading_buy_handler(context, trader, trading)
        else:
            transaction_history += trading_sell_handler(context, trader,
                                                        trading)
    return transaction_history


def trading_buy_handler(context, trader, trading):
    stock = trader.buy(trading)
    if stock is not None:
        context.buy_stocks([stock])


def trading_sell_handler(context, trader, trading):
    transactions = trader.sell(trading)
    remained_stocks = copy.deepcopy(context.basket)
    returned_budget = 0

    for trans in transactions:
        remaining_sold_amount = trans.amount
        updated_basket = {}
        for owned_stock in remained_stocks.values():
            # Stock code is not matched
            if owned_stock.code != trans.code:
                updated_basket[owned_stock.code] = owned_stock
                continue
            # Stock is more than sold amount
            if owned_stock.amount > trans.amount:
                returned_budget += trans.sold_price * trans.amount
                owned_stock.update_amount(owned_stock.amount - trans.amount)
                updated_basket[owned_stock.code] = owned_stock
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


def _parse_datetime(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%d')


def _get_ticks(start_date, end_date, feature_manager):
    print('Extract stock opened dates from KOSPI...')
    # Filter date by KOSPI to decide if stock market is opened at specific date.
    kospi_df = feature_manager.get_candle_data('KS11', start_date, end_date)
    return kospi_df.index.tolist()


def simulate(start_date, end_date, trade_algorithm, budget):
    print(f'Simulation date range: {start_date} ~ {end_date}')
    start_date = _parse_datetime(start_date)
    end_date = _parse_datetime(end_date)

    context = algorithm.Context(budget=budget, basket=[])
    feature_manager = feature_manager_helper.FinanceDataReaderManager(
        'KRX', cache_start_date=start_date, cache_end_date=end_date)
    metric_manager = MetricManager(
        budget=budget, feature_manager=feature_manager)
    trader = trading_manager.get_trading_manager(
        'back_test', {'feature_manager': feature_manager})

    transaction_history = []
    for now in tqdm.tqdm(_get_ticks(start_date, end_date, feature_manager)):
        context.update_market_time(now)
        trader.set_user_and_stock_data(context, None)
        transaction_history += algorithm_handler(trade_algorithm, context,
                                                 trader, feature_manager)

        metric_manager.update_metric_by_context(context)
        # print(context)
    # print(transaction_history)
    metric_manager.report()
    metric_manager.plot_profit_rate(comparisons=['KOSPI', 'KOSDAQ'])


def main(args):
    del args  # Unused

    #trade_algorithm = algorithm.DummyAlgorithm()
    trade_algorithm = multi_factor_market_timing.MultiFactorMarketTiming()
    simulate(FLAGS.start_date, FLAGS.end_date, trade_algorithm, FLAGS.budget)


if __name__ == '__main__':
    app.run(main)
