import requests


class BadRequestException(Exception):
    """Bad request to ViaggiaTreno API."""

    def __init__(self, status_code: int, response: str, *args: object) -> None:
        """Creates a BadRequestException.

        Args:
            status_code (int): the response status code
            response (str): the response data
        """
        self.status_code = status_code
        self.response = response
        super().__init__(*args)


class ViaggiaTrenoAPI:
    BASE_URL: str = "http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/"

    def __init__(self) -> None:
        pass

    @staticmethod
    def _raw_request(method: str, *parameters: str) -> str:
        """Perform a HTTP request to ViaggiaTreno API and return a raw string,
        if the request has been successful.

        Args:
            method (str): the method to be called
            parameters (tuple[str]): a list of parameters

        Raises:
            BadRequestException: if the request returns a non-200 status code

        Returns:
            str: the raw response from the API
        """
        response: requests.Response = requests.get(
            f"{ViaggiaTrenoAPI.BASE_URL}{method}/{'/'.join(parameters)}"
        )

        if response.status_code != 200:
            raise BadRequestException(
                status_code=response.status_code,
                response=response.text,
            )

        return response.text
