from gufe.settings.models import SettingsBaseModel


class StrategySettings(SettingsBaseModel):

    def __init__(self):
        normalize_weights: bool = True
