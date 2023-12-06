from alter_ego.agents import *
from alter_ego.structure import Conversation
from alter_ego.utils import extract_number, from_file
from alter_ego.exports.otree import link as ai

from otree.api import *

import random


doc = """
EGO, with a human second mover
"""


class C(BaseConstants):
    NAME_IN_URL = "ego_human"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 10


class Treatment:
    both_cooperate = 20
    both_defect = 8
    sucker = 0
    temptation = 28


class Subsession(BaseSubsession):
    pass


def creating_session(subsession):
    for player in subsession.get_players():
        if player.round_number == 1:
            player.participant.vars["dropout"] = False
            player.participant.vars["clerpay_amount"] = 1.00  # for dropouts

            player.treatment = random.choice([1, 3, 4])

            llm = GPTThread(
                model="gpt-4",
                temperature=1.0,
                name="AI",
            )
            human = ExternalThread(name="Human")

            convo = Conversation(llm=llm, human=human)
            convo.all.treatment = Treatment
            convo.all.num_rounds = C.NUM_ROUNDS

            llm.system(
                from_file(
                    f"ego_human/prompts/prompts00{player.treatment}/pd_seq/system_c.txt"
                )
            )
            human.system(
                from_file(
                    f"ego_human/prompts/prompts00{player.treatment}/pd_seq/system_h.txt"
                )
            )

            ai(player.participant).set(convo)
            player.llm_id = str(llm.id)
        else:
            player.treatment = player.in_round(1).treatment


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    llm_id = models.StringField()
    treatment = models.IntegerField()

    choice = models.IntegerField(
        initial=-1, choices=[[1, "OPTION 1"], [2, "OPTION 2"]], label="Your Choice"
    )

    other_choice = models.IntegerField()


def invoke_first_mover(player):
    with ai(player.participant) as convo:
        response = extract_number(
            convo.llm.submit(
                from_file(
                    f"ego_human/prompts/prompts00{player.treatment}/pd_seq/first_mover.txt"
                ),
                player=player,
            ),
        )

        player.other_choice = convo.llm.last = response

        convo.human.submit(
            from_file(
                f"ego_human/prompts/prompts00{player.treatment}/pd_seq/second_mover.txt"
            ),
            player=player,
        )


# PAGES
class Start(Page):
    timeout_seconds = 450

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.participant.vars["dropout"] = True

            return


class SecondMover(Page):
    timeout_seconds = 300

    form_fields = ["choice"]
    form_model = "player"

    @staticmethod
    def vars_for_template(player):
        # should be "before_this_page"…

        if player.field_maybe_none("other_choice") is None:
            invoke_first_mover(player)

    @staticmethod
    def js_vars(player):
        with ai(player.participant) as convo:
            return dict(history=convo.human.history)

    @staticmethod
    def app_after_this_page(player, upcoming_apps):
        if player.participant.vars["dropout"]:
            return "clerpay_end"

    @staticmethod
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.participant.vars["dropout"] = True

            return

        with ai(player.participant) as convo:
            convo.human.last = player.choice

            # Determine payoffs

            if player.other_choice == 1 and player.choice == 1:
                convo.llm.payoff = Treatment.both_cooperate
                player.payoff = Treatment.both_cooperate
            elif player.other_choice == 1 and player.choice == 2:
                convo.llm.payoff = Treatment.sucker
                player.payoff = Treatment.temptation
            elif player.other_choice == 2 and player.choice == 1:
                convo.llm.payoff = Treatment.temptation
                player.payoff = Treatment.sucker
            elif player.other_choice == 2 and player.choice == 2:
                convo.llm.payoff = Treatment.both_defect
                player.payoff = Treatment.both_defect

            convo.human.submit(
                from_file(
                    f"ego_human/prompts/prompts00{player.treatment}/pd_seq/result.txt"
                ),
                player=player,
            )  # only relevant for final round!


class Result(Page):
    timeout_seconds = 300

    @staticmethod
    def is_displayed(player):
        return (
            player.round_number == C.NUM_ROUNDS
            and not player.participant.vars["dropout"]
        )

    @staticmethod
    def js_vars(player):
        with ai(player.participant) as convo:
            return dict(history=convo.human.history)


class End(Page):
    timeout_seconds = 300

    @staticmethod
    def is_displayed(player):
        if not player.participant.vars["dropout"]:
            player.participant.vars["clerpay_amount"] = float(
                player.participant.payoff_plus_participation_fee()
            )

            return player.round_number == C.NUM_ROUNDS
        else:
            return False


page_sequence = [Start, SecondMover, Result, End]
