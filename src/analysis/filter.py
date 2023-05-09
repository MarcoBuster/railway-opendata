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


from datetime import datetime

import pandas as pd


def date_filter(
    df: pd.DataFrame, start_date: datetime | None, end_date: datetime | None
) -> pd.DataFrame:
    """Filter dataframe by date (day).

    Args:
        df (pd.DataFrame): the considered dataframe
        start_date (datetime | None): the start date
        end_date (datetime | None): the end date

    Returns:
        pd.DataFrame: the filtered dataframe
    """
    if isinstance(start_date, datetime):
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        df = df.loc[df.day >= start_date]
    if isinstance(end_date, datetime):
        end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        df = df.loc[df.day <= end_date]
    return df


def railway_company_filter(
    df: pd.DataFrame, railway_companies: str | None
) -> pd.DataFrame:
    """Filter dataframe by the railway company.

    Args:
        df (pd.DataFrame): the considered dataframe
        client_codes (str | None): a comma-separated list of client names

    Returns:
        pd.DataFrame: the filtered dataframe
    """
    if not railway_companies or len(railway_companies) < 1:
        return df

    code_list: list[str] = [
        s.strip().lower() for s in railway_companies.strip().split(",") if len(s) > 0
    ]
    return df.loc[df.client_code.str.lower().isin(code_list)]
