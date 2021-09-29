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

    def get_feature(self,
                    code: str,
                    feature_name: str,
                    start: Optional[str] = None,
                    end: Optional[str] = None):
        """Get feature value"""
        if feature_name not in self.CANDLE_FEATURES:
            raise ValueError('Invalid feature request: {feature_name}')
        return self.get_candle_data(code, start, end)[feature_name]

    def get_candle_data(self,
                        code: str,
                        start: Optional[str] = None,
                        end: Optional[str] = None) -> pd.DataFrame:
        """Get Candle data"""
        return fdr.DataReader(code, start, end)
