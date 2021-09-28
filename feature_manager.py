"""Manage various features for stock trading"""

from absl import logging


class FeatureManager:

    def __init__(self):
        pass

    def get_feature(self, code: str, feature_name: str, when: int):
        logging.info(f'Get {feature_name} for {code} at {when}')
