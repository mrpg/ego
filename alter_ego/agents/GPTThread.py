from typing import Any
import openai
import os
import sys
import time

from alter_ego.agents import APIThread
import alter_ego.utils

client = openai.OpenAI(api_key="")


class GPTThread(APIThread):
    """
    Class representing a GPT-3 or GPT-4 Thread.
    """

    def __init__(self, model, temperature, *args, **kwargs) -> None:
        if "extra_for_module" in kwargs:
            for k, v in kwargs["extra_for_module"]:
                setattr(openai, k, v)

        if "extra_for_client" in kwargs:
            for k, v in kwargs["extra_for_client"]:
                setattr(client, k, v)

        super().__init__(*args, model=model, temperature=temperature, **kwargs)

        if "api_key" not in kwargs:
            self.api_key = self.get_api_key()

    def get_api_key(self) -> str:
        """
        Retrieve the OpenAI API key.

        :return: The OpenAI API key.
        :rtype: str
        :raises ValueError: If API key is not found.
        """
        if "OPENAI_KEY" in os.environ:
            return os.environ["OPENAI_KEY"]
        elif os.path.exists("openai_key"):
            return alter_ego.utils.from_file("openai_key")
        elif os.path.exists("api_key"):
            return alter_ego.utils.from_file("api_key")
        else:
            raise ValueError(
                "If not specified within the GPTThread constructor (argument api_key), OpenAI API key must be specified in the environment variable OPENAI_KEY, or any of the files openai_key or api_key."
            )

    def send(
        self, role: str, message: str, max_tokens: int = 500, **kwargs: Any
    ) -> str:
        """
        Submit the user message, get the response from the model, and memorize it.

        :param role: Role of the sender ("user").
        :type role: str
        :param message: The user's message to submit.
        :type message: str
        :param max_tokens: Maximum number of tokens for the model to generate.
        :type max_tokens: int
        :keyword kwargs: Additional keyword arguments.
        :type kwargs: Any
        :return: The model's response.
        :rtype: str
        """
        if role == "user":
            time.sleep(self.delay)

            llm_out = self.get_model_output(message, max_tokens)

            response = llm_out.choices[0].message.content

            self.memorize("assistant", response)

            return response

    def get_model_output(self, message: str, max_tokens: int) -> str:
        """
        Get the model output for the given message.

        :param message: The user's message.
        :type message: str
        :param max_tokens: Maximum number of tokens for the model to generate.
        :type max_tokens: int
        :return: The model output.
        :rtype: str
        """
        client.api_key = self.api_key

        try:
            if self.verbose:
                print("+", end="", file=sys.stderr, flush=True)

            llm_out = client.chat.completions.create(
                model=self.model,
                messages=self.history,
                max_tokens=max_tokens,
                n=1,
                stop=None,
                temperature=self.temperature,
            )

            if llm_out.choices[0].finish_reason != "stop":
                raise ValueError("GPT finished early")

            self.log.append(llm_out)

            return llm_out
        except Exception as e:
            self.log.append(e)

            raise e  # re-raise
