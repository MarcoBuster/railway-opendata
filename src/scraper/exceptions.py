# railway-opendata: scrape and analyze italian railway data
# Copyright (C) 2023 Marco Aceti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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


class IncompleteTrenordStopDataException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
