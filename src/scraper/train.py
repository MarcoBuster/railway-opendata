import src.scraper.station as st


class Train:
    """A ViaggiaTreno train.

    Attributes:
        number (int): the train number
        origin (Station): the departing station
        destination (Station | None): the arriving station
        category (str | None): e.g. REG, FR, IC...
        running (bool | None): true if the train departed but not yet arrived
        cancelled (bool | None): true if the train has been cancelled (partially or totally)
    """

    def __init__(self, number: int, origin: st.Station) -> None:
        """Initialize a new train

        Args:
            number (int): the train number
            origin (Station): the departing station

        Notes:
            Other fields can be setted manually.
        """
        self.number: int = number
        self.origin: st.Station = origin
        self.destination: st.Station | None = None
        self.category: str | None = None
        self.running: bool | None = None
        self.cancelled: bool | None = None

    @classmethod
    def _from_station_departures_arrivals(cls, train_data: dict) -> "Train":
        train: Train = cls(
            number=train_data["numeroTreno"],
            origin=st.Station.by_code(train_data["codOrigine"]),
        )
        train.category = train_data["categoriaDescrizione"].upper().strip()
        train.running = train_data["circolante"]
        train.cancelled = train_data["provvedimento"] != 0
        return train

    def __repr__(self) -> str:
        return f"Treno [{'R' if self.running else 'S'}{'X' if self.cancelled else ''}] {self.category} {self.number} : {self.origin} -> ?"
