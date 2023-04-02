import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pandas.core.groupby.generic import DataFrameGroupBy

from src.const import WEEKDAYS


def describe(df: pd.DataFrame | DataFrameGroupBy) -> None:
    """Call pandas.DataFrame.describe()"""
    print(df.describe())


def delay_boxplot(df: pd.DataFrame | DataFrameGroupBy) -> None:
    """Show a seaborn boxplot of departure and arrival delays"""
    sns.set_theme(style="ticks", palette="pastel")
    sns.set()

    if isinstance(df, DataFrameGroupBy):
        grouped_by: str = df.any().index.name
        group_melt = pd.DataFrame()

        grouped: list = list(df)  # type: ignore
        if grouped_by == "weekday":
            # Re-order fields
            grouped.sort(key=lambda t: WEEKDAYS[t[0]])

        for group in grouped:  # type: ignore
            melt = pd.melt(
                group[1],
                id_vars=[
                    col
                    for col in df.obj.columns
                    if col
                    not in [
                        "arrival_delay",
                        "departure_delay",
                    ]
                ],
                value_name="value",
            )
            group_melt = pd.concat([group_melt, melt])

        ax = sns.boxplot(
            group_melt[[grouped_by, "variable", "value"]],
            x=grouped_by,
            y="value",
            hue="variable",
            showfliers=False,
        )
        ax.set(xlabel=grouped_by, ylabel="Delay (minutes)")

    elif isinstance(df, pd.DataFrame):
        ax = sns.boxplot(
            df[["arrival_delay", "departure_delay"]],
            showfliers=False,
        )
        ax.set(xlabel="Variable", ylabel="Delay (minutes)")

    plt.grid()
    plt.show()
