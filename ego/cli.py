#!/usr/bin/env python3

import click
import csv
import importlib
import os
import pickle
import sys

from importlib.machinery import SourceFileLoader
from pathlib import Path


@click.group()
def main():
    pass


@main.command(help="Run a scenario.")
@click.argument("scenario")
@click.option(
    "--times", "-n", default=1, type=int, help="Number of replications (times to run)."
)
@click.option(
    "--param",
    "-p",
    multiple=True,
    type=(str, int),
    help="Optional parameters for scenario.",
)
def run(scenario, times, param):
    if scenario.isidentifier():
        try:
            scenario = importlib.import_module(f"scenarios.{scenario}")
        except ModuleNotFoundError:
            target = f"{scenario}.py"

            loader = SourceFileLoader(scenario, target)
            scenario = loader.load_module()

        scenario.run(times=times, **dict(param))
    else:
        raise ValueError("Invalid scenario.")


@main.command(help="Export experimental data to stdout.")
@click.argument("scenario")
@click.argument("experiment")
def data(scenario, experiment):
    if scenario.isidentifier():
        try:
            scenario = importlib.import_module(f"scenarios.{scenario}")
        except ModuleNotFoundError:
            target = f"{scenario}.py"

            loader = SourceFileLoader(scenario, target)
            scenario = loader.load_module()

        files = (
            f
            for f in Path(os.path.join("out", experiment)).rglob("*.pkl")
            if f.is_file()
        )

        data = []

        for filename in sorted(files):
            with open(filename, "rb") as f:
                thr = pickle.load(f)
                e = scenario.export(thr)

                if isinstance(e, dict):
                    data.append(dict(experiment=experiment, thread=thr.id) | e)
                else:
                    for row in e:
                        data.append(dict(experiment=experiment, thread=thr.id) | row)

        all_keys = set()

        for row in data:
            all_keys.update(row.keys())

        all_keys = sorted(all_keys)

        writer = csv.DictWriter(sys.stdout, fieldnames=all_keys)
        writer.writeheader()

        for row in data:
            writer.writerow(row)

        print(f"Wrote {len(data)} lines.", file=sys.stderr)
    else:
        raise ValueError("Invalid scenario.")


if __name__ == "__main__":
    main()
