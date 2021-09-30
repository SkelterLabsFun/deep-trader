"""Perform trading"""

import abc
import dataclasses
from datetime import date
from typing import List, Optional

from absl import logging

import algorithm


class SecuritiesManager:
    pass


@dataclasses.dataclass
class Transaction:
    code: str
    bought_price: int
    sold_price: int
    amount: int
    bought_at: date
    sold_at: date


class TradingManager(abc.ABC):

    def __init__(self):
        self.initialize()

    def initialize(self):
        # TODO(inyoup): write proper intialization code for each TradingManager.
        pass

    @abc.abstractmethod
    def buy(self, trading: algorithm.Trading) -> Optional[algorithm.Stock]:
        raise NotImplementedError()

    @abc.abstractmethod
    def sell(self, trading: algorithm.Trading) -> List[Transaction]:
        raise NotImplementedError()

    # TODO(jseo): Check the following method
    def get_transactions(self):
        return self._transactions


class DaishinTradingManager(TradingManager):
    pass


class BackTestTradingManager(TradingManager):
    # NOTE(inyoup): Implement real stock purchase mechanism. In demo days,
    #   we suppose all attempts to buy stock will success.

    def __init__(self):
        self._context = None
        self._stock_data = None

    def set_user_and_stock_data(self, context: algorithm.Context, stock_data):
        # TODO(inyoup): Implement to fecth market data from SecuritiesManager
        #   after implemented.
        self._context = context
        self._stock_data = stock_data

    def get_market_time(self):
        return self._context.market_time

    def buy(self, trading: algorithm.Trading) -> Optional[algorithm.Stock]:
        self.log(f'Call buy API for {trading}')
        return algorithm.Stock(
            code=trading.code,
            bought_price=trading.target_price,
            amount=trading.amount,
            bought_at=self.get_market_time(),
        )  # always succeed to buy

    def sell(self, trading: algorithm.Trading) -> List[Transaction]:
        self.log(f'Call sell API for {trading}')
        return self._selling_to_transaction(trading)

    def _selling_to_transaction(self, trading):
        transactions = []

        selling_amount = trading.amount
        for owned_stock in self._context.basket:
            if owned_stock.code != trading.code:
                continue

            if selling_amount > owned_stock.amount:
                selling_amount_for_owned_stock = owned_stock.amount
                selling_amount -= owned_stock.amount
            else:
                selling_amount_for_owned_stock = selling_amount
                selling_amount = 0

            transaction = Transaction(
                code=owned_stock.code,
                bought_price=owned_stock.bought_price,
                sold_price=trading.target_price,
                amount=selling_amount_for_owned_stock,
                bought_at=owned_stock.bought_at,
                sold_at=self.get_market_time())
            transactions.append(transaction)
            if selling_amount == 0:
                break
        return transactions

    def log(self, log_str):
        pass
        # print(f'[BackTestTradingManager] {log_str}')


def get_trading_manager(trading_manager_type: str) -> TradingManager:
    if trading_manager_type == 'daishin':
        return DaishinTradingManager()
    if trading_manager_type == 'back_test':
        return BackTestTradingManager()
    raise NotImplementedError(
        f'Unsupported TradingManagerType: {trading_manager_type}')
