import json
import random
import uuid
from alter_ego.structure import Conversation
from itertools import product
from typing import Any, Dict, List, Optional, Type


class Experiment:
    """
    Class for managing an Experiment, which links treatments to conversations.
    """

    def __init__(self, *treatments: Type) -> None:
        """
        Initialize the Experiment.

        :param treatments: Variable-length list of treatment classes.
        :type treatments: Type
        :raises ValueError: If less than two treatments are supplied.
        :raises AttributeError: If treatments have incongruent attributes.
        """
        if len(treatments) < 2:
            raise ValueError("Experiment expects at least two treatments.")

        if any(hasattr(t, "__dict__") for t in treatments):
            keys = set(treatments[0].__dict__.keys())

            for treatment in treatments:
                if set(treatment.__dict__.keys()) != keys:
                    raise AttributeError(
                        f"Treatment {treatment.__name__} is incongruent."
                    )

        self.id = uuid.uuid4()
        self.treatments = treatments
        self.params: Dict[str, List[str]] = {}

    def link(self, convo: Conversation, treatment: Optional[Type] = None) -> None:
        """
        Associate a treatment and parameters with a Conversation object.

        :param convo: The conversation to which to link the treatment and parameters.
        :type convo: Conversation
        :param treatment: The treatment to apply; None for random selection.
        :type treatment: Optional[Type]
        """
        if treatment is None:
            convo.all.treatment = random.choice(self.treatments)
        else:
            convo.all.treatment = treatment

        convo.all.experiment = self

        for param, values in self.params.items():
            randomized_values = random.sample(values, len(values))

            assert len(randomized_values) >= len(convo.threads)

            for thread, value in zip(convo.threads, randomized_values):
                setattr(thread, param, value)

    def param(self, name: str, values: List[Any]) -> None:
        """
        Set a named parameter for the experiment.

        :param name: The name of the parameter to set.
        :type name: str
        :param values: A list of values to assign to the parameter.
        :type values: List[Any]
        """
        self.params[name] = values

    def run(
        self,
        agent_factory,
        filter=json.loads,
        times=1,
        *,
        outcome="result",
        keep_retval=False,
        **kwargs,
    ) -> List[Dict]:
        data = []

        if filter is None:
            filter = lambda x: x

        for _ in range(times):
            for treat in self.treatments:
                an_agent = agent_factory()
                retval = an_agent.user(treat.prompt, **treat.data, **kwargs)

                extra = {} if not keep_retval else {"retval": retval}

                try:
                    from_agent = filter(retval)
                except Exception as e:
                    from_agent = None

                if isinstance(from_agent, dict):
                    data.append(treat.data | from_agent | extra)
                else:
                    data.append(treat.data | {outcome: from_agent} | extra)

        return data


class GenericTreatment:
    def __init__(self, prompt, **kwargs):
        self.prompt = prompt
        self.data = kwargs


def factorial(prompt, **kwargs) -> Experiment:
    keys = kwargs.keys()

    return Experiment(
        *[
            GenericTreatment(prompt=prompt, **dict(zip(keys, values)))
            for values in product(*kwargs.values())
        ]
    )
