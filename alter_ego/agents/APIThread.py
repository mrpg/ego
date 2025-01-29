from typing import Any
import abc
import os
import time

import alter_ego.structure
import alter_ego.utils


class APIThread(alter_ego.structure.Thread, abc.ABC):
    """
    Abstract base class representing any Thread accessible using an API.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the APIThread.

        :param args: Additional arguments.
        :type args: Any
        :param kwargs: Additional keyword arguments, includes `api_key`, `delay`, and `verbose`.
        :type kwargs: Any
        """
        self.log = []  # Initialize log

        self.delay = kwargs.get("delay", 0)
        self.verbose = kwargs.get("verbose", False)

        super().__init__(*args, **kwargs)

    @abc.abstractmethod
    def send(
        self, role: str, message: str, max_tokens: int = 500, **kwargs: Any
    ) -> str:
        """
        Abstract method to send a message to a role.

        :param role: The role of the message sender.
        :type role: str
        :param message: The message to send.
        :type message: str
        :param max_tokens: Maximum number of tokens for the message.
        :type max_tokens: int
        :keyword kwargs: Additional keyword arguments.
        :type kwargs: Any
        :return: The response message.
        :rtype: str
        """
        pass

    @abc.abstractmethod
    def get_model_output(self, message: str, max_tokens: int) -> Any:
        """
        Abstract method to get the model's output.

        :param message: The input message to the model.
        :type message: str
        :param max_tokens: Maximum number of tokens for the output.
        :type max_tokens: int
        :return: The model's output.
        :rtype: Any
        """
        pass
