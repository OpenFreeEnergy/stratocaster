from gufe import AlchemicalNetwork, ProtocolResult
from gufe.transformations import Transformation, NonTransformation

# if including validators with settings, recommended
from pydantic import Field, field_validator

from stratocaster.base import Strategy, StrategyResult
from stratocaster.base.models import StrategySettings


class MyCustomStrategySettings(StrategySettings):

    # an example settings field
    max_runs: int = Field(
        default=1,
        description="the number of times each transformation will run",
    )

    # validate your field
    @field_validator("max_runs", mode="before")
    def validate_max_runs(cls, value):
        if value <= 0:
            raise ValueError("max_runs must be larger than 0")
        return value


class MyCustomStrategy(Strategy):

    # required: prevents initialization of the strategy with incorrect
    # settings at runtime
    _settings_cls = MyCustomStrategySettings

    @classmethod
    def _default_settings(cls) -> StrategySettings:
        # the model provides the defaults
        return MyCustomStrategySettings()

    def _propose(
        self,
        alchem_network: AlchemicalNetwork,
        protocol_results: dict[Transformation | NonTransformation, ProtocolResult]
    ) -> StrategyResult:
        ...
