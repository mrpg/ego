import os
from typing import Any, Dict, List, Optional, Union
from alter_ego.structure import Thread, Conversation
from alter_ego.utils import to_html

# Constants for key formats
PLAYER_KEY_FORMAT = "__alter_ego/player/{}/{}"
GROUP_KEY_FORMAT = "__alter_ego/group/{}/{}"
ROUND_KEY_FORMAT = "__alter_ego/round/{}/{}"
PARTICIPANT_KEY_FORMAT = "__alter_ego/participant"
SESSION_KEY_FORMAT = "__alter_ego/session"

OUTPATH = ".ego_output/"
NO_SAVE = False
FULL_SAVE = True


def html_history(thread: Thread) -> None:
    """Convert thread history to HTML format."""
    thread.html_history = [
        {role: to_html(message) for role, message in record.items()}
        for record in thread._history
    ]


def save(thread: Thread) -> None:
    """Save the thread data."""
    if not NO_SAVE:
        outdir = OUTPATH + thread.metadata["otree_session"]

        # save json backup
        thread.save(outdir=outdir, full_save=False)

        if FULL_SAVE:
            # also save pickle
            thread.save(outdir=outdir, full_save=True)


def add_hooks(thread: Thread) -> None:
    """Add history hooks to a thread."""
    thread.history_hooks.add(html_history)
    thread.history_hooks.add(save)


class Assigner:
    """
    A class for attribute assignment operations.
    """

    def __init__(
        self, assignees: List[Any], key: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize an instance of Assigner.

        :param assignees: A list of objects to be assigned.
        :param key: The key used for assigning.
        """
        self.assignees = assignees
        self.key = key
        self.metadata = metadata if metadata is not None else dict()

    def __bool__(self) -> bool:
        """Check if the key exists in the first assignee's vars dict."""
        return self.key in self.assignees[0].vars

    def __enter__(self) -> Any:
        self.value = self.assignees[0].vars[self.key]

        return self.value

    def __exit__(self, *args: Any) -> bool:
        self.set(self.value)

        return False

    def set(self, value: Union[Thread, Conversation]) -> None:
        """Assign value to the 'vars' dictionary of all assignees."""
        if isinstance(value, Conversation):
            for thread in value:
                thread.metadata |= self.metadata
                add_hooks(thread)
        elif isinstance(value, Thread):
            value.metadata |= self.metadata
            add_hooks(value)
        else:
            raise NotImplementedError(
                "Only a Thread or a Conversation can be assigned."
            )

        for assignee in self.assignees:
            assignee.vars[self.key] = value

    def unset(self) -> None:
        """Unset the key in all assignees."""
        for assignee in self.assignees:
            if self.key in assignee.vars:
                del assignee.vars[self.key]


def link(instance: Any) -> Assigner:
    """
    Create an Assigner object linked to the given instance.

    :param instance: The instance to be linked.
    :returns: An Assigner object.
    :raises NotImplementedError: If instance type is unsupported.
    """
    metadata = dict(otree_session=instance.session.code)
    super_names = [s.__name__ for s in instance.__class__.mro()]

    if "BasePlayer" in super_names:
        targets = [instance.participant]
        metadata["participant"] = instance.participant.id_in_session
        key_in_vars = PLAYER_KEY_FORMAT.format(
            instance.__module__, instance.round_number
        )
    elif "BaseGroup" in super_names:
        targets = [p.participant for p in instance.get_players()]
        metadata["group"] = instance.id_in_subsession
        key_in_vars = GROUP_KEY_FORMAT.format(
            instance.__module__, instance.round_number
        )
    elif "BaseSubsession" in super_names:
        targets = [p.participant for p in instance.get_players()]
        metadata["subsession"] = instance.round_number
        key_in_vars = ROUND_KEY_FORMAT.format(
            instance.__module__, instance.round_number
        )
    elif "Participant" in super_names:
        targets = [instance]
        metadata["participant"] = instance.id_in_session
        key_in_vars = PARTICIPANT_KEY_FORMAT
    elif "Session" in super_names:
        targets = [instance]
        metadata["session"] = instance.code
        key_in_vars = SESSION_KEY_FORMAT
    else:
        raise NotImplementedError(
            f"Instance of type {type(instance).__name__} not recognized. "
            "Target can only be a Player, Participant, Group, Subsession, or Session."
        )

    return Assigner(targets, key_in_vars, metadata)
