import json
import os
import random
import sys
import time
from typing import Any

import alter_ego.agents
import alter_ego.experiment
import alter_ego.structure

from games import pd
from games.pd import treatments

e = alter_ego.experiment.Experiment(
    *treatments.all,
)

e.param("name", ["James", "John", "Robert", "Michael", "William", "David", "Richard"])


def run(times: int, model: str) -> None:
    """
    Run the experiment with multiple replications.

    Parameters
    ----------
    model : str
        The model to be used for the agents.

    This function initializes agents, runs conversations, and handles exceptions.
    """
    print("Note: This scenario runs as per the preregistration, ignoring --times/-n.")
    os.mkdir(f"out/{e.id}")

    pairs_per_frame: int = 200
    rounds: int = 10

    t = list(e.treatments) * pairs_per_frame  # balanced treatment assignment
    random.shuffle(t)

    replications: int = len(t)

    for i in range(replications):
        while True:
            try:
                a1 = alter_ego.agents.GPTThread(
                    model=model, temperature=1.0, delay=1, verbose=True
                )
                a2 = alter_ego.agents.GPTThread(
                    model=model, temperature=1.0, delay=1, verbose=True
                )

                convo = alter_ego.structure.Conversation(a1, a2)

                e.link(convo, t[i])

                print(f"Replication {i+1} of {replications}.", file=sys.stderr)

                pd.iterated(convo, rounds)

                convo.all.save(e.id)
                break
            except RuntimeError:
                print("RuntimeError occurred. Retrying.", file=sys.stderr)

                convo.all.tainted = True
                convo.all.save(e.id)

                time.sleep(15)

    print(f"Experiment {e.id} OK", file=sys.stderr)


def export(thread: alter_ego.agents.GPTThread) -> list[dict]:
    data = []

    row_template = dict(  # define variables of interest here
        convo=thread.convo.id,
        thread_type=thread.__class__.__name__,
        treatment=thread.treatment.t,
    )

    if not thread.tainted:
        min_time = min(e.created for e in thread.log if hasattr(e, "created"))  # HACK

        for choice in thread.choices:
            data.append(row_template | choice | dict(min_time=min_time))
    else:
        print(f"Skipping tainted thread {thr.id}.", file=sys.stderr)

    return data
