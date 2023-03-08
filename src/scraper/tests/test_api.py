import pytest
from src.scraper import ViaggiaTrenoAPI, BadRequestException


def test_bad_request():
    with pytest.raises(BadRequestException):
        ViaggiaTrenoAPI._raw_request("invalid", "method")


def test_ok_request():
    response: str = ViaggiaTrenoAPI._raw_request("regione", "S01700")
    assert type(response) == str
    assert int(response) == 1
