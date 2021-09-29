"""Manage various features for stock trading"""
import abc
from typing import Optional

import FinanceDataReader as fdr
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
