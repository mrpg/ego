from typing import Any, List

import sys
import alter_ego.utils


def iterated(convo: "Conversation", rounds: int = 10) -> None:
    """
    Run an iterated game for a given conversation and number of rounds.

    Parameters
    ----------
    convo : Any
        The conversation object containing the agents and treatment.
    rounds : int, optional
        The number of rounds to play, default is 10.

    This function handles the game logic, agent choices, and payoffs.
    """
    treat = convo.treatment

    convo.all.num_rounds = rounds
    convo.all.system(treat.system)

    for round_ in range(1, rounds + 1):
        print(f"Round {round_}.", end=" ", file=sys.stderr, flush=True)
        choices: List[int] = []

        for thr in convo:
            try:
                # Try including feedback from previous round
                msg: str = thr.preamble
            except AttributeError:
                msg = ""

            if convo.now == 1:
                msg += treat.first_mover
            else:
                msg += treat.second_mover

            msg = thr.prepare(msg, round_=round_)

            # Submit question, obtain LLM's choice

            while True:  # Re-run this until a valid response is given:
                convo.all.last = alter_ego.utils.extract_number(thr.submit(msg))

                if convo.all.last in [1, 2]:
                    convo.all.last = int(convo.all.last)
                    break
                else:
                    msg = (
                        'Your response was invalid. Always exclusively respond with "OPTION 1" or "OPTION 2". Do not repeat the question. Do not give any explanation. Here the previous message is repeated:'
                        + msg
                    )

            choices.append(convo.all.last)

        # Determine treatment-based payoffs
        if choices[0] == 1 and choices[1] == 1:
            convo.threads[0].payoff = treat.both_cooperate
            convo.threads[1].payoff = treat.both_cooperate
        elif choices[0] == 1 and choices[1] == 2:
            convo.threads[0].payoff = treat.sucker
            convo.threads[1].payoff = treat.temptation
        elif choices[0] == 2 and choices[1] == 1:
            convo.threads[0].payoff = treat.temptation
            convo.threads[1].payoff = treat.sucker
        elif choices[0] == 2 and choices[1] == 2:
            convo.threads[0].payoff = treat.both_defect
            convo.threads[1].payoff = treat.both_defect

        for thr in convo:
            # Feedback about this round, for next round
            thr.preamble = (
                thr.prepare(
                    treat.result,
                    round_=round_,
                    own=choices[convo.now - 1],
                    otherchoice=choices[1 - (convo.now - 1)],
                )
                + "\n\n"
            )

            # Record machine-readable choice
            thr.choices.append(dict(round_=round_, choice=choices[convo.now - 1]))

    print(file=sys.stderr)
