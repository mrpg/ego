from typing import Any, Dict, Optional
import json
import os
import requests
import sys
import time

from alter_ego.agents import APIThread


class TextSynthThread(APIThread):
    """
    Class representing a TextSynth Thread.
    """

    def __init__(self, **kwargs: Any):
        """
        Initialize the TextSynthThread.

        :keyword kwargs: Additional keyword arguments.
        :type kwargs: Any
        """
        # defaults
        self.endpoint = "https://api.textsynth.com/v1/engines/falcon_40B-chat/chat"
        self.temperature = 1.0

        super().__init__(**kwargs)

    def ts_data(self) -> Dict[str, Any]:
        """
        Prepare the data for TextSynth API call.

        :return: Data to be sent in the API request.
        :rtype: Dict[str, Any]
        :raises ValueError: If an invalid history item is encountered.
        """
        system_set = False
        next_role = 1

        data = dict(messages=[])

        for item in self._history:
            if item["role"] == "system" and not system_set:
                data["system"] = item["content"]
                system_set = True
            elif item["role"] == "user" and next_role == 1:
                data["messages"].append(item["content"])
                next_role = 2
            elif item["role"] == "assistant" and next_role == 2:
                data["messages"].append(item["content"])
                next_role = 1
            else:
                raise ValueError(f"The following history item is invalid: {item}")

        return data

    def send(
        self,
        role: str,
        message: str,
        max_tokens: int = 500,
        extra_params: Optional[Dict[str, Any]] = None,
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

            llm_out = self.get_model_output(message, max_tokens, extra_params)

            response = llm_out["text"]

            self.memorize("assistant", response)

            return response

    def get_model_output(
        self,
        message: str,
        max_tokens: int,
        extra_params: Optional[Dict[str, Any]] = None,
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

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            params = {
                "max_tokens": max_tokens,
                "temperature": self.temperature,
            } | (extra_params if extra_params is not None else {})

            rq = requests.post(
                self.endpoint,
                headers=headers,
                data=json.dumps(self.ts_data() | params),
            )

            llm_out = rq.json()
            self.log.append(llm_out)

            return llm_out
        except Exception as e:
            self.log.append(e)

            raise e  # re-raise
