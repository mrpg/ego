from alter_ego.agents import *
from alter_ego.utils import from_file
from alter_ego.exports.otree import link as ai

from otree.api import *


doc = """
Interact with AI
"""


class C(BaseConstants):
    NAME_IN_URL = "ego_chat"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


def creating_session(subsession):
    for player in subsession.get_players():
        # here we associate a "Thread" with an oTree object
        # can associate Threads with: players, groups, participants, subsessions, sessions

        # this here is an actual GPT model by OpenAI, put the API key in the
        # project directory, file "api_key"

        ai(player).set(GPTThread(model="gpt-4", temperature=1.0))

        # this here is a very stupid "constant" thread that always gives the
        # same response

        # ai(player).set(ConstantThread(response="Lol!", model="ConstantThread"))

        # there are some others as well, e.g. a CLIThread, see alter_ego.agents


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    name = models.StringField(label="Your name")


# PAGES
class Welcome(Page):
    form_fields = ["name"]
    form_model = "player"

    def before_next_page(player, timeout_happened):
        with ai(player) as llm:
            # this sets the "system" prompt
            llm.system(
                from_file("ego_chat/prompts/system.txt"), player=player
            )  # can pass objects to prompts! The templating engine used is actually (much) more powerful than oTree's


class Chat(Page):
    def live_method(player, data):
        if isinstance(data, str):
            with ai(player) as llm:
                # this submits the player's message
                response = llm.submit(data, max_tokens=500)

                # note: if you put the AI on the "group" object or somewhere other than
                # the player, you may want to change this
                return {player.id_in_group: [True, response]}

    def vars_for_template(player):
        with ai(player) as llm:
            return {"ai": llm}


page_sequence = [Welcome, Chat]
