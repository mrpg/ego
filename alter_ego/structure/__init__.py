from abc import ABC, abstractmethod
from typing import Callable, Dict, Iterator, List, Set, Tuple, Union, Any
from jinja2 import Environment, StrictUndefined
from alter_ego.structure.Relay import Relay
import copy
import uuid
import os
import pickle
import json

VALID_ROLES = ["system", "user", "assistant"]


class Thread(ABC):
    """
    Abstract base class representing a Thread.
    """

    def __init__(self, **params: Any) -> None:
        """
        Initialize a Thread instance.

        :param params: Arbitrary keyword parameters.
        """
        # Initialize instance variables
        self.__dict__ |= params
        self.id: uuid.UUID = uuid.uuid4()
        self.metadata: Dict[str, Any] = {}
        self._history: List[Dict[str, str]] = []
        self.tainted: bool = False
        self.convo = None  # Will be assigned later
        self.history_hooks: Set[Callable] = set()
        self.choices: List[Any] = []
        self.env: Environment = Environment(undefined=StrictUndefined)

    def __repr__(self) -> str:
        """
        :return: String representation of the Thread.
        """
        return f"<{self.__class__.__name__}/{self.name if 'name' in self.__dict__ else str(self.id)[0:8]}>"

    @property
    def history(self) -> List[Dict[str, str]]:
        """
        :return: Deep copy of message history.
        """
        return copy.deepcopy(self._history)

    def memorize(self, role: str, message: str) -> None:
        """
        Memorizes a message and its associated role.

        :param role: Role of the message ('system', 'user', or 'assistant').
        :param message: Message content.
        :raises ValueError: If the role is invalid or if a system message already exists.
        """
        if role not in VALID_ROLES:
            raise ValueError(f'Invalid role "{role}".')

        if role == "system" and any(item["role"] == "system" for item in self.history):
            raise ValueError(f"System message already set.")

        self._history.append({"role": role, "content": message})
        for f in self.history_hooks:
            f(self)

    def prepare(self, template: str, **extra: Any) -> str:
        """
        Prepare a template with additional parameters.

        :param template: Template string.
        :param extra: Additional parameters to inject into the template.
        :return: Rendered template string.
        """
        template = self.env.from_string(template)
        return template.render(**extra, **self.__dict__)

    def save(
        self, subdir: str = ".", outdir: str = "out", full_save: bool = True
    ) -> None:
        """
        Saves the current Thread into a file.

        :param subdir: The sub-directory to save the file in.
        :param outdir: The main directory to save the file in.
        :param full_save: Whether to save as pickle (True) or JSON (False).
        :raises ValueError: If the Thread is not part of a Conversation.
        """
        if self.convo is None:
            target_dir = f"{outdir}/{subdir}"
        else:
            target_dir = f"{outdir}/{subdir}/{self.convo.id}"

        os.makedirs(target_dir, exist_ok=True)

        outfile = (
            f"{target_dir}/{self.id}.pkl"
            if full_save
            else f"{target_dir}/{self.id}.json"
        )
        mode = "wb" if full_save else "w"

        with open(outfile, mode) as fp:
            if full_save:
                pickle.dump(self, fp)
            else:
                json.dump(dict(history=self.history, metadata=self.metadata), fp)

    def cost(self) -> float:
        """
        Computes and returns the cost associated with the Thread.

        :returns: The cost, 0.0 for this base implementation. Adjust in subclasses.
        """
        raise NotImplementedError

    def system(self, message: str, **kwargs: Any) -> Any:
        """
        Sends a system-level message.

        :param message: The message to send.
        :param kwargs: Additional keyword arguments for message preparation.
        :returns: Return value from the send method.
        """
        self.memorize("system", m := self.prepare(message, **kwargs))

        retval = self.send("system", m, **kwargs)

        return retval

    def user(self, message: str, **kwargs: Any) -> Any:
        """
        Sends a user-level message.

        :param message: The message to send.
        :param kwargs: Additional keyword arguments for message preparation.
        :returns: Return value from the send method.
        """
        self.memorize("user", m := self.prepare(message, **kwargs))

        retval = self.send("user", m, **kwargs)

        return retval

    def assistant(self, message: str, **kwargs: Any) -> Any:
        """
        Sends an assistant-level message.

        :param message: The message to send.
        :param kwargs: Additional keyword arguments for message preparation.
        :returns: Return value from the send method.
        """
        self.memorize("assistant", m := self.prepare(message, **kwargs))

        retval = self.send("assistant", m, **kwargs)

        return retval

    def submit(self, message: str, **kwargs: Any) -> Any:
        """
        Submits a message as a user and sends it after preparation.

        :param message: The message to submit.
        :param kwargs: Additional keyword arguments for message preparation.
        :returns: Return value from the send method.
        """
        self.memorize("user", m := self.prepare(message, **kwargs))

        retval = self.send("user", m, **kwargs)

        return retval

    @abstractmethod
    def send(self, role: str, message: str, **kwargs: Any) -> Any:
        """
        Abstract method that must be implemented by subclasses to send messages.

        :param role: Role of the sender, can be 'system', 'user', or 'assistant'.
        :param message: The message to be sent.
        :param kwargs: Additional keyword arguments.
        :returns: Implementation dependent.
        """
        pass


class Conversation:
    """
    Class encapsulating a Conversation consisting of multiple Threads.
    """

    def __init__(self, *threads: Thread, **named_threads: Thread) -> None:
        """
        Initialize a Conversation object.

        :param threads: Thread instances as positional arguments.
        :param named_threads: Thread instances as named arguments.
        :raises ValueError: If both 'threads' and 'named_threads' are used, or none of them are used.
        """
        if (len(threads) > 0 and len(named_threads) > 0) or (
            len(threads) == 0 and len(named_threads) == 0
        ):
            raise ValueError(
                "You may only use 'threads' or 'named_threads', not both, not neither."
            )

        if len(threads) > 0:
            self.threads = tuple(threads)
        else:
            self.threads = tuple(named_threads.values())
            self.__dict__ |= named_threads

        self.now = 1
        self.all = Relay(self, self.threads)
        self.id = uuid.uuid4()

        for thread in self.threads:
            thread.convo = self

            if len(self.threads) == 2:
                thread.other = (
                    self.threads[1] if thread == self.threads[0] else self.threads[0]
                )
            elif len(self.threads) > 2:
                thread.others = [t for t in self.threads if t != thread]

    def __iter__(self) -> Iterator[Thread]:
        """
        Create an iterator for traversing through the Threads in this Conversation.

        :yields: Each Thread in the Conversation.
        """
        for j, thread in enumerate(self.threads, 1):
            self.now = j
            yield thread
