"""Multi factor Market timing

Ref:
https:#www.intelliquant.co.kr/article/870?forum=0
"""

import datetime
from typing import List

from absl import logging
import numpy as np
import pandas as pd
from pykrx import stock as krx_stock

import algorithm

_Trading = algorithm.Trading


class MultiFactorMarketTiming(algorithm.Algorithm):

    def __init__(self):
        self._stock_basket = None
        self._stock_num = 20  # 주식 종목 수
        self._stock_weight = 0.98  # 주식 비중 (거래비용 고려 현금 2% 확보)
        self._draw_down_flag = False
        self._current_total_equity = 0
        # 시뮬레이션 시작일에 바로 포트폴리오 신규 구성을 하기 위해 사용될 상태 변수
        self._is_first = True
        self._context = None

    def _is_rebalancing_day(self) -> bool:
        # TODO(jseo): we only support Monthly schedule now
        # TODO(jseo): Deal with if the first day of month is a holiday
        return self._context.market_time.day == 1

    def run(self, context, features) -> List[algorithm.Trading]:
        del features  # Unused
        self._context = context

        draw_down_effect = self._kosdaq_filter()
        logging.debug(f'draw_down: {draw_down_effect}')
        if draw_down_effect:
            return draw_down_effect
        # TODO(jseo): LossCut

        if not self._is_rebalancing_day() and not self._is_first:
            logging.debug(
                f'[{context.market_time}] Skipped: {self._is_rebalancing_day()}'
                f' / {self._is_first}')
            return []

        trading_list = []
        if not self._draw_down_flag or self._is_first:
            self._is_first = False
            self._stock_basket = []
            #context.update_budget(self._current_total_equity *
            #                      self._stock_weight)
            codes = self._build_portfolio()
            logging.debug(f'build_portfolio: {codes}')
            from_date = self._context.market_time
            close_prices = krx_stock.get_market_ohlcv_by_ticker(
                from_date, market='ALL')
            close_prices = close_prices['종가']
            for code in codes:
                to_date = from_date + datetime.timedelta(1)
                try:
                    #close_price = float(
                    #    krx_stock.get_market_ohlcv_by_date(
                    #        self._convert_date_to_pykrx_format(from_date),
                    #        self._convert_date_to_pykrx_format(to_date),
                    #        code)['종가'][0])
                    close_price = float(close_prices[code])
                except Exception as ex:
                    logging.error(
                        f'Error on market ohlcv: {from_date}, {to_date}, {code}'
                    )
                    raise Exception() from ex
                budget = context.budget * self._stock_weight // self._stock_num
                amount = budget // close_price

                if code in self._context.basket:
                    prev_stock = self._context.basket[code]
                    diff_amount = amount - prev_stock.amount
                    if diff_amount > 0:
                        trading_list.append(
                            _Trading(
                                code=code,
                                target_price=close_price,
                                bound_price=close_price * 1.1,
                                amount=diff_amount,
                                action='buy'))
                    elif diff_amount < 0:
                        diff_amount *= -1
                        trading_list.append(
                            _Trading(
                                code=code,
                                target_price=close_price,
                                bound_price=close_price * 0.9,
                                amount=diff_amount,
                                action='sell'))
                else:
                    trading_list.append(
                        _Trading(
                            code=code,
                            target_price=close_price,
                            bound_price=close_price * 1.1,
                            amount=amount,
                            action='buy'))
        logging.debug(f'[{context.market_time}] {trading_list}')
        return trading_list

    @staticmethod
    def _convert_date_to_pykrx_format(date):
        return date.strftime('%Y%m%d')

    # TODO(jseo): separate filters as another file
    @staticmethod
    def _china_stock_filter(stock_code: str) -> bool:
        return stock_code[0] != '9'

    def _build_portfolio(self) -> List[str]:
        universe = krx_stock.get_market_ticker_list(
            self._convert_date_to_pykrx_format(self._context.market_time))
        universe = filter(self._china_stock_filter, universe)
        universe = list(universe)
        # '012710' seems closed
        closed_companies = ['012710', '011260', '015545', '012095', '002535', '016167', '012405']
        for closed in closed_companies:
            if closed in universe:
                universe.remove(closed)
        #logging.debug(f'universe: {universe}')
        fundamentals = krx_stock.get_market_fundamental_by_ticker(
            self._convert_date_to_pykrx_format(self._context.market_time),
            market='ALL')
        logging.debug(f'fundamentals-1: {fundamentals}')
        fundamentals = fundamentals[fundamentals.index.isin(universe)]
        logging.debug(f'fundamentals-2: {fundamentals}')
        #fundamentals = fundamentals[fundamentals.PER > 0.5]
        #fundamentals = fundamentals[fundamentals.PBR > 0.2]
        #logging.debug(f'fundamentals-3: {fundamentals}')
        fundamentals['per_rank'] = fundamentals['PER'].rank(method='dense')
        fundamentals['pbr_rank'] = fundamentals['PBR'].rank(method='dense')
        logging.debug(f'fundamentals: {fundamentals}')

        caps = krx_stock.get_market_cap_by_ticker(
            self._convert_date_to_pykrx_format(self._context.market_time))
        caps = caps[caps.index.isin(fundamentals.index)]
        caps['cap_rank'] = caps['시가총액'].rank(method='dense')
        logging.debug(f'caps: {caps}')

        data = pd.concat([fundamentals, caps], axis=1)
        data['rank_sum'] = data['cap_rank'] + (data['per_rank'] +
                                               data['pbr_rank']) / 2.0
        data = data.sort_values(by=['rank_sum'])
        portfolio = data.head(n=self._stock_num)
        logging.debug(f'Build portfolio: {portfolio}')
        return portfolio.index.to_list()

    def _kosdaq_filter(self):
        kosdaq_ticker = '2001'
        to_date = self._context.market_time
        # TODO(jseo): Implement working day counter
        # Before that, we retrieves more days than we need.
        from_date = to_date - datetime.timedelta(30)
        try:
            kosdaq = krx_stock.get_index_ohlcv_by_date(
                self._convert_date_to_pykrx_format(from_date),
                self._convert_date_to_pykrx_format(to_date), kosdaq_ticker)
        except:
            logging.error(f'Error fetching index: {from_date}/{to_date}')
            return []
        ma_3 = np.mean(kosdaq['종가'][-3:])
        ma_5 = np.mean(kosdaq['종가'][-5:])
        ma_10 = np.mean(kosdaq['종가'][-10:])
        closest_close = kosdaq['종가'][-1]

        tradings = []
        if (closest_close < ma_3 and closest_close < ma_5 and
                closest_close < ma_10):
            self._stock_weight = 0
            logging.info(f'코스닥 하락장 발생!! 코스닥 종가: {closest_close} '
                         f'3일이평: {ma_3} 5일이평: {ma_5} 10일이평: {ma_10}')
            from_date = self._convert_date_to_pykrx_format(
                self._context.market_time)
            close_prices = krx_stock.get_market_ohlcv_by_ticker(
                from_date, market='ALL')
            close_prices = close_prices['종가']
            for stock in self._context.basket.values():
                # TODO(jseo): get_market_ohlcv_by_date occur some error
                #close_price = krx_stock.get_market_ohlcv_by_date(
                #    from_date, to_date, stock.code)['종가'][0]
                try:
                    close_price = close_prices[stock.code]
                except KeyError as ex:
                    logging.error(f'Keys: {close_prices.index}')
                    raise KeyError() from ex

                tradings.append(
                    algorithm.Trading(
                        code=stock.code,
                        target_price=close_price,
                        bound_price=close_price * 0.9,
                        amount=stock.amount,
                        action='sell'))
            self._draw_down_flag = True
        else:
            logging.info(f'코스닥 하락장 종료!!')
            self._stock_weight = 0.98
            if self._draw_down_flag:
                #self._current_total_equity = 0  # TODO
                self._draw_down_flag = False
