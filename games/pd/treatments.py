from typing import List, Type

import alter_ego.utils


class Baseline:
    """
    Baseline class for defining the basic structure of a treatment.
    """

    first_mover: str = alter_ego.utils.from_file("prompts/pd_seq/first_mover")
    second_mover: str = alter_ego.utils.from_file("prompts/pd_seq/second_mover")
    result: str = alter_ego.utils.from_file("prompts/pd_seq/result")

    both_cooperate: int = 20
    both_defect: int = 8
    sucker: int = 0
    temptation: int = 28


all: List[Type[Baseline]] = []

for t in range(1, 11):
    # read frames
    cls: str = f"T{t}"

    globals()[cls] = type(
        cls,
        (Baseline,),
        dict(t=t, system=alter_ego.utils.from_file(f"prompts/pd_seq/system{t}")),
    )

    all.append(globals()[cls])
