"""Manage various features for stock trading"""
import abc
from typing import Optional

from pykrx import stock
import FinanceDataReader as fdr
import numpy as np
import pandas as pd


class FeatureManager:
    CANDLE_FEATURES = ['Open', 'Close', 'High', 'Low', 'Volume', 'Change']
    COMPANY_FEATURES = []
    FEATURES = CANDLE_FEATURES + COMPANY_FEATURES

    def __init__(self, market: str):
        """Initialize feature manager"""
        self._market = market

    @abc.abstractmethod
    def get_feature(self,
                    code: str,
                    feature_name: str,
                    start: Optional[str] = None,
                    end: Optional[str] = None):
        raise NotImplementedError()


# TODO(jseo): Separate as another modulea
class FinanceDataReaderManager(FeatureManager):

    def __init__(self,
                 market: str,
                 cache_start_date: Optional[str] = None,
                 cache_end_date: Optional[str] = None):
        
        super(FinanceDataReaderManager, self).__init__(market)

        self._cache_start_date = cache_start_date
        self._cache_end_date = cache_end_date
        self._cache = {}

    def _is_cache_used(self):
        return (self._cache_start_date is not None and
                self._cache_end_date is not None)

    def _has_cached_data(self, code, start, end):
        if not self._is_cache_used():
            return False

        is_loaded = code in self._cache
        in_range = (start >= self._cache_start_date and
                    end <= self._cache_end_date)
        return is_loaded and in_range

    def get_feature(self,
                    code: str,
                    feature_name: str,
                    start: Optional[str] = None,
                    end: Optional[str] = None):
        """Get feature value"""
        if feature_name not in self.CANDLE_FEATURES:
            raise ValueError('Invalid feature request: {feature_name}')
        return self.get_candle_data(code, start, end)[feature_name]

    def get_feature_at(self, code: str, feature_name: str, time: str):
        if not self._is_cache_used():
            return fdr.DataReader(code, time, time)
        if self._has_cached_data(code, time, time):
            candle_df = self._cache[code]
        else:
            candle_df = fdr.DataReader(code, self._cache_start_date,
                                       self._cache_end_date)
            self._cache[code] = candle_df
        
        try:
            return candle_df[feature_name][time]
        except KeyError:
            return None

    def get_candle_data(self,
                        code: str,
                        start: Optional[str] = None,
                        end: Optional[str] = None) -> pd.DataFrame:
        """Get Candle data"""
        if not self._is_cache_used():
            return fdr.DataReader(code, start, end)

        if self._has_cached_data(code, start, end):
            # print('use cached data')
            candle_df = self._cache[code]
        else:
            candle_df = fdr.DataReader(code, self._cache_start_date,
                                       self._cache_end_date)
            self._cache[code] = candle_df

        index_list = candle_df.index.to_pydatetime()
        index_filter = ((index_list >= start) & (index_list <= end))
        return candle_df.loc[index_filter]


class AnnualFundamentalDataManager(FeatureManager):
    FUNDAMENTAL_FEATURES = [
        'corp_name', 'year', 'total_equity', 'sales', 'profit', 'net_income',
        'bps', 'per', 'eps', 'debt_ratio', 'profit_ratio'
    ]

    def __init__(self,
                 market : str,
                 filepath: str):
        super().__init__(market)
        self._fundamental_df = pd.read_csv(
            filepath,
            sep='\t',
            index_col='year',
            dtype={
                'code': str,
                'corp_name': str,
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

    def _get_year(self, dt):
        return pd.to_datetime(dt).year

    def get_feature(self,
                    code: str,
                    feature_name: str,
                    start: Optional[str] = None,
                    end: Optional[str] = None):
        """Get feature value"""
        if feature_name not in self.FUNDAMENTAL_FEATURES:
            raise ValueError(f'Invalid feature request: {feature_name}')
        start = self._get_year(start)
        end = self._get_year(end)
        return self.get_fundamental_data(code, start, end)[feature_name]

    def get_fundamental_data(self,
                             code: str,
                             start: Optional[int] = None,
                             end: Optional[int] = None) -> pd.DataFrame:
        """Get annual fundamental data"""
        df = self._fundamental_df[self._fundamental_df['code'] == code]
        if start:
            df = df[df.index >= start]
        if end:
            df = df[df.index <= end]
        return df


class FundamentalDataManager(FeatureManager):
    FUNDAMENTAL_FEATURES = ['BPS', 'PER', 'PBR', 'EPS', 'DIV', 'DPS']

    def _convert_datetime_str(self, dt):
        return pd.to_datetime(dt).strftime('%Y%m%d')

    def get_feature(self,
                    code: str,
                    feature_name: str,
                    start: str,
                    end: str):
        """Get feature value"""
        if feature_name not in self.FUNDAMENTAL_FEATURES:
            raise ValueError(f'Invalid feature request: {feature_name}')
        start = self._convert_datetime_str(start)
        end = self._convert_datetime_str(end)
        return self.get_fundamental_data(code, start, end)[feature_name]

    def get_fundamental_data(self,
                             code: str,
                             start: str,
                             end: str,
                             freq: Optional[str] = 'd') -> pd.DataFrame:
        """Get fundamental data

        Args:
            code: stock code
            start: date time string
            end: date time string
            freq: d - 일 / m - 월 / y - 년
        """
        return stock.get_market_fundamental_by_date(start, end, code, freq)
