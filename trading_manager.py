"""Perform trading"""

from absl import logging

from experimental.demodays2021.deep_traders import algorithm


class TradingManager:

    def __init__(self):
        pass

    def buy(self, trading: algorithm.Trading):
        logging.info(f'Call buy API for {trading}')

    def sell(self, trading: algorithm.Trading):
        logging.info(f'Call sell API for {trading}')
