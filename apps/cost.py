from pathlib import Path
from typing import Any


def total_cost(experiment: str) -> float:
    """
    Calculate the total cost of an experiment in USD.

    Parameters
    ----------
    experiment : str
        The identifier for the experiment whose cost is to be calculated.

    Returns
    -------
    float
        The total cost of the experiment in USD.

    This function iterates through all the pickled files in the output directory
    for the given experiment, summing up the costs.
    """
    usd: float = 0.0
    path: Path = Path(os.path.join("out", experiment))

    for outfile in sorted(path.glob("**/*.pkl")):
        with open(outfile, "rb") as pkl:
            thr: Any = pickle.load(pkl)
            usd += thr.cost()

    return usd
