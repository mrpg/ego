import json
import os
import random
import sys
import time
import traceback

import alter_ego.agents
import alter_ego.experiment
import alter_ego.structure
import alter_ego.utils

from dataclasses import dataclass


with open(os.getenv("BUILT_FILE", "built.json")) as f:
    definition = json.load(f)


@dataclass
class Treatment:
    name: str
    variables: dict = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


def make_treatment(definition: dict, treatment_name: str) -> Treatment:
    treat = Treatment(name=treatment_name)

    for var, in_treatment in definition["variables"].items():
        treat.variables[var] = in_treatment[treatment_name]

    return treat


def make_thread(thread_str: str):
    if thread_str == "CLIThread":
        return alter_ego.agents.CLIThread(verbose=True)
    elif thread_str == "GPTThread (GPT 3.5)":
        return alter_ego.agents.GPTThread(
            model="gpt-3.5-turbo", temperature=1, verbose=True
        )
    elif thread_str == "GPTThread (GPT 4)":
        return alter_ego.agents.GPTThread(model="gpt-4", temperature=1, verbose=True)
    else:
        raise ValueError(f"{thread_str} not found.")


def make_filter(filter_def: list):
    if filter_def[0] == "JSON":
        return json.loads
    elif filter_def[0] == "extract_number":
        return alter_ego.utils.extract_number
    elif filter_def[0] == "exclusive_response":

        def new_exclusive_response(s):
            return alter_ego.utils.exclusive_response(s, filter_def[1].split(";"))

        return new_exclusive_response
    elif filter_def[0] == "As is":
        return lambda s: s


def run(times: int = 1) -> None:
    treatments = [make_treatment(definition, t) for t in definition["treatments"]]
    e = alter_ego.experiment.Experiment(*treatments)

    for i in range(1, times + 1):
        threads = []

        for i_, thrstr in definition["threads"]:
            thread = make_thread(thrstr)
            threads.append(thread)

            thread.i = i_

        convo = alter_ego.structure.Conversation(*threads)

        e.link(convo)  # randomly assign treatment

        convo.all.rounds = definition["rounds"]

        convo.all.system(
            alter_ego.utils.homogenize(definition["prompts"]["system"]),
            **convo.treatment.variables,
        )

        try:
            for round_ in range(1, definition["rounds"] + 1):
                convo.all.round = round_

                for index, thread in enumerate(threads):
                    text_response = thread.submit(
                        alter_ego.utils.homogenize(definition["prompts"]["user"]),
                        **convo.treatment.variables,
                    )
                    filtered = make_filter(definition["filters"][index])(text_response)

                    thread.choices.append(filtered)

                    if filtered is None:
                        raise ValueError(
                            f"Thread returned bad response: '{text_response}', not filtered with {definition['filters'][index]}"
                        )
        except Exception as exc:
            traceback.print_exception(*sys.exc_info())
            convo.all.tainted = True

        convo.all.save(e.id)
        print(file=sys.stderr)

    print(f"Experiment {e.id} OK", file=sys.stderr)


def export(thread: alter_ego.structure.Thread) -> list[dict]:
    data = []

    row_template = dict(  # define variables of interest here
        convo=thread.convo.id,
        thread_type=thread.__class__.__name__,
        tainted=thread.tainted,
        treatment=thread.treatment.name,
        i=thread.i,
    )

    for round_, choice in enumerate(thread.choices, 1):
        data.append(row_template | dict(round=round_, choice=json.dumps(choice)))

    return data
