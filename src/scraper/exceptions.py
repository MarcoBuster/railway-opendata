class BadRequestException(Exception):
    """Bad request to ViaggiaTreno API."""

    def __init__(
        self, url: str, status_code: int, response: str, *args: object
    ) -> None:
        """Creates a BadRequestException.

        Args:
            url (str): the request URL
            status_code (int): the response status code
            response (str): the response data
        """
        self.url = url
        self.status_code = status_code
        self.response = response
        super().__init__(*args)
