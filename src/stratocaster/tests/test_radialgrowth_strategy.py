from stratocaster.strategies.radialgrowth import (
    RadialGrowthStrategy,
)

from stratocaster.tests.utils import StrategyTestMixin


class TestRadialGrowth(StrategyTestMixin):
    strategy_class = RadialGrowthStrategy
