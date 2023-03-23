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
