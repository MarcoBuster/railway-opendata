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


import argparse
import typing as t
from pathlib import Path


def _arg_or_default(args: argparse.Namespace, field: str, default: t.Any) -> t.Any:
    if not hasattr(args, field) or not getattr(args, field):
        return default

    return getattr(args, field)


def parse_input_format_output_args(
    args: argparse.Namespace,
) -> t.Tuple[Path, Path, str]:
    input_f: Path = Path(args.pickle_file)
    format: str = _arg_or_default(args, "format", "csv")
    output_f: Path = Path(
        _arg_or_default(
            args,
            "output_file",
            input_f.parents[0] / input_f.name.replace("pickle", format),
        )
    )
    return input_f, output_f, format
