"""Algorithm class"""

import dataclasses
from typing import List


@dataclasses.dataclass
class Trading:
    code: str
    target_price: float
    bound_price: float  # used for upper/lower bound for deal
    amount: int
    # TODO(jseo): Convert as Enum
    action: str  # buy or sell


# TODO(jseo): Consider to change as protobuf
class Algorithm:
    """Quant algorithm

    This determines which list of items buy/sell.
    """

    def __init__(self):
        pass

    # TODO(jseo): Modify name
    def run(self, features) -> List[Trading]:
        return []
