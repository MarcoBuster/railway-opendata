class Station:
    """A ViaggiaTreno station."""

    def __init__(self, station_data: dict) -> None:
        self._raw: dict = station_data
