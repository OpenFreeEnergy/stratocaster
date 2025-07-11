from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey
from openff.units import unit

from stratocaster.base import Strategy, StrategyResult
from stratocaster.base.models import StrategySettings

try:
    from pydantic.v1 import Field, validator
except ImportError:
    from pydantic import (
        Field,
        validator,
    )

import pydantic


class UncertaintyStrategySettings(StrategySettings):
    """Specific settings required for the UncertaintyStrategy."""

    target_uncertainty: unit.Quantity = Field(
        default=0.5 * unit.kilocalorie_per_mole, 
        description="Target uncertainty threshold; transformations with higher uncertainty get priority"
    )
    min_samples: int = Field(
        default=3,
        description="Minimum number of protocol DAG results before considering uncertainty"
    )
    max_uncertainty_cap: unit.Quantity = Field(
        default=5.0 * unit.kilocalorie_per_mole,
        description="Maximum uncertainty cap; transformations above this are considered problematic"
    )
    max_samples: int = Field(
        default=20,
        description="Maximum number of protocol DAG results before stopping regardless of uncertainty"
    )

    @validator("target_uncertainty")
    def validate_target_uncertainty(cls, value):
        # Convert to kcal/mol for validation if needed
        if hasattr(value, 'to'):
            value_in_kcal_mol = value.to(unit.kilocalorie_per_mole).magnitude
        else:
            # Assume it's already in kcal/mol if no units
            value_in_kcal_mol = float(value)
            value = value * unit.kilocalorie_per_mole
        
        if not (0 < value_in_kcal_mol <= 10):
            raise ValueError("`target_uncertainty` must be between 0 and 10 kcal/mol")
        return value

    @validator("min_samples")
    def validate_min_samples(cls, value):
        if not (1 <= value <= 100):
            raise ValueError("`min_samples` must be between 1 and 100")
        return value

    @validator("max_uncertainty_cap")
    def validate_max_uncertainty_cap(cls, value):
        # Convert to kcal/mol for validation if needed
        if hasattr(value, 'to'):
            value_in_kcal_mol = value.to(unit.kilocalorie_per_mole).magnitude
        else:
            # Assume it's already in kcal/mol if no units
            value_in_kcal_mol = float(value)
            value = value * unit.kilocalorie_per_mole
        
        if not (0 < value_in_kcal_mol <= 20):
            raise ValueError("`max_uncertainty_cap` must be between 0 and 20 kcal/mol")
        return value

    @validator("max_samples")
    def validate_max_samples(cls, value):
        if not (1 <= value <= 1000):
            raise ValueError("`max_samples` must be between 1 and 1000")
        return value


class UncertaintyStrategy(Strategy):
    """A Strategy that prioritizes Transformations based on their uncertainty.
    
    This strategy assigns higher weights to transformations with uncertainty
    above a target threshold, and removes weights for transformations
    that have achieved the desired precision, are considered problematic,
    or have exceeded the maximum number of samples.
    
    Transformations are prioritized as follows:
    - No results yet: maximum priority (weight = 1.0)
    - Below minimum samples: maximum priority (weight = 1.0)
    - Above maximum samples: no priority (weight = None, hard termination)
    - Above uncertainty cap: no priority (weight = None, likely problematic)
    - Above target uncertainty: scaled priority based on excess uncertainty
    - Below target uncertainty: no priority (weight = None, sufficient precision)
    
    The max_samples parameter ensures guaranteed termination, preventing unbounded
    sampling for transformations that may not converge to the target uncertainty.
    """

    _settings_cls = UncertaintyStrategySettings

    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[GufeKey, ProtocolResult],
    ) -> StrategyResult:
        """Propose Transformation weight recommendations based on uncertainty.

        Parameters
        ----------
        alchemical_network: AlchemicalNetwork
            The network containing transformations to prioritize
        protocol_results: dict[GufeKey, ProtocolResult]
            A dictionary whose keys are the GufeKeys of Transformations in the AlchemicalNetwork
            and whose values are the ProtocolResults for those Transformations.

        Returns
        -------
        StrategyResult
            A StrategyResult containing the proposed Transformation weights.
        """
        settings = self.settings
        assert isinstance(settings, UncertaintyStrategySettings)

        alchemical_network_mdg = alchemical_network.graph
        weights: dict[GufeKey, float | None] = {}

        for state_a, state_b in alchemical_network_mdg.edges():
            # Get the transformation key from the edge
            transformation_key = alchemical_network_mdg.get_edge_data(state_a, state_b)[0]["object"].key
            
            # Get the protocol result for this transformation
            result = protocol_results.get(transformation_key)
            
            if result is None:
                # No results yet - highest priority
                weights[transformation_key] = 1.0
                continue
            
            # Check if we have minimum samples
            if result.n_protocol_dag_results < settings.min_samples:
                weights[transformation_key] = 1.0
                continue
            
            # Check if we've exceeded maximum samples (hard termination)
            if result.n_protocol_dag_results >= settings.max_samples:
                weights[transformation_key] = None
                continue
            
            # Get uncertainty from the result
            uncertainty = result.get_uncertainty()
            
            # Ensure uncertainty has units for comparison
            if not hasattr(uncertainty, 'to'):
                # Assume uncertainty is in kcal/mol if no units
                uncertainty = uncertainty * unit.kilocalorie_per_mole
            
            # Cap extremely high uncertainties (might indicate problematic transformations)
            if uncertainty > settings.max_uncertainty_cap:
                weights[transformation_key] = None
                continue
            
            # Calculate weight based on uncertainty vs target
            if uncertainty > settings.target_uncertainty:
                # Scale weight by how much uncertainty exceeds target
                excess_uncertainty = uncertainty - settings.target_uncertainty
                weight = min(1.0, (excess_uncertainty / settings.target_uncertainty).magnitude)
                weights[transformation_key] = weight
            else:
                # Below target uncertainty - sufficient precision achieved
                weights[transformation_key] = None
        
        return StrategyResult(weights=weights)

    @classmethod
    def _default_settings(cls) -> StrategySettings:
        return UncertaintyStrategySettings()