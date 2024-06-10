from ollama import Client

import json
import os
import requests
import sys
import time

from alter_ego.agents import APIThread
from typing import Any, Dict, List, Optional


class OllamaThread(APIThread):
    """
    Class representing a Ollama Thread.
    """

    def __init__(self, **kwargs: Any):
        """
        Initialize the OllamaThread.

        :keyword kwargs: Additional keyword arguments.
        :type kwargs: Any
        """
        # defaults
        self.endpoint = "http://localhost:11434"
        self.timeout = 60
        self.model = "llama3"

        super().__init__(**kwargs)

    def ollama_data(self) -> List[Dict[str, str]]:
        """
        Prepare the data for Ollama API call.

        :return: Data to be sent in the API request.
        :rtype: Dict[str, Any]
        :raises ValueError: If an invalid history item is encountered.
        """
        system_set = False
        next_role = 1

        messages = []

        for item in self._history:
            if item["role"] == "system" and not system_set:
                messages.append(dict(role="system", content=item["content"]))
                system_set = True
            elif item["role"] == "user" and next_role == 1:
                messages.append(dict(role="user", content=item["content"]))
                next_role = 2
            elif item["role"] == "assistant" and next_role == 2:
                messages.append(dict(role="assistant", content=item["content"]))
                next_role = 1
            else:
                raise ValueError(f"The following history item is invalid: {item}")

        return messages

    def send(
        self,
        role: str,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Submit the user message, receive the model's response, and memorize it.

        :param role: Role of the sender ("user").
        :type role: str
        :param message: The user's message.
        :type message: str
        :param max_tokens: Maximum number of tokens for the model to generate.
        :type max_tokens: int
        :param extra_params: Additional parameters for the model.
        :type extra_params: Optional[Dict[str, Any]]
        :keyword kwargs: Additional keyword arguments.
        :type kwargs: Any
        :return: The model's response.
        :rtype: str
        """
        if role == "user":
            time.sleep(self.delay)

            llm_out = self.get_model_output(message, options)

            response = llm_out["message"]["content"]

            self.memorize("assistant", response)

            return response

    def get_model_output(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Get the model output for the given message.

        :param message: The user's message.
        :type message: str
        :param max_tokens: Maximum number of tokens for the model to generate.
        :type max_tokens: int
        :param extra_params: Additional parameters for the model.
        :type extra_params: Optional[Dict[str, Any]]
        :return: The model output.
        :rtype: Any
        """

        try:
            if self.verbose:
                print("+", end="", file=sys.stderr, flush=True)

            client = Client(host=self.endpoint, timeout=self.timeout)

            llm_out = client.chat(
                model="llama3", messages=self.ollama_data(), options=options
            )
            self.log.append(llm_out)

            return llm_out
        except Exception as e:
            self.log.append(e)

            raise e  # re-raise
