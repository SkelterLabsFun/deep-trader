"""Algorithm class"""

import copy
import dataclasses
from datetime import date
from typing import List


@dataclasses.dataclass
class Trading:
    code: str
    target_price: float
    bound_price: float  # used for upper/lower bound for deal
    amount: int
    # TODO(jseo): Convert as Enum
    action: str  # buy or sell

@dataclasses.dataclass
class Stock:
    code: str
    bought_price: int
    amount: int
    bought_at: date

    def update_amount(self, amount):
        self.amount = amount

class Context:
    """Context to represent current status."""

    def __init__(self, budget=0, basket=[], market_time=None):
        self.budget = budget
        self.basket = basket
        self.market_time = market_time
    
    def __str__(self):
        return ''.join([
            f'<Context at {self.market_time}, budget={self.budget}, ',
            f'basket_count={len(self.basket)}>\n',
            f'Owned stocks:\n',
            '\n'.join([f' - {stock}' for stock in self.basket])
        ])
    
    def update_budget(self, budget):
        self.budget = budget

    def update_basket(self, basket):
        self.basket = copy.deepcopy(basket)

    def update_market_time(self, market_time):
        self.market_time = market_time
    
    def buy_stocks(self, stocks: List[Stock]):
        total_price = 0
        for stock in stocks:
            total_price += stock.bought_price * stock.amount
        self.budget -= total_price
        self.basket.extend(stocks)


# TODO(jseo): Consider to change as protobuf
class Algorithm:
    """Quant algorithm

    This determines which list of items buy/sell.
    """

    def __init__(self):
        pass

    # TODO(jseo): Modify name
    def run(self, context, features) -> List[Trading]:
        return []

class DummyAlgorithm(Algorithm):
    """Dummy Quant algorithm"""
    cnt = 0

    def run(self, context, features) -> List[Trading]:
        self.cnt += 1
        to_buy = self.cnt % 2 == 1
        return [Trading(code="SKELTER_LABS",
                       target_price=5000 + self.cnt,
                       bound_price=5100 + self.cnt,
                       amount=10,
                       action='buy' if to_buy else 'sell')]
