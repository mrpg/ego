import shutil
from typing import Any, Union
import alter_ego.structure
from colorama import Fore, Back, init

init(autoreset=True)


class ConstantThread(alter_ego.structure.Thread):
    """
    Class representing a thread that always returns the same response.

    This class extends the Thread class in the alter_ego.structure module.
    """

    def send(self, role: str, message: str) -> Union[str, None]:
        """
        Memorize the message and the assistant's response, then return the response.

        :param role: The role of the sender ("system" or "user").
        :param message: The message to memorize.
        :return: The assistant's response if role is "user", otherwise None.
        :rtype: Union[str, None]
        :raises NotImplementedError: If role is not "system" or "user".
        """
        cli = hasattr(self, "cli") and self.cli  # Determine if the CLI mode is active

        if role == "system" and cli:
            print(Back.RED + f"System instructions for {self}:")
            print(message)
            print()
        elif role == "user":
            response = self.response

            if cli:
                print(Back.RED + f"Message for {self}:")
                print(message)
                print()

                print(Back.GREEN + f"{self}'s response:")
                print(response)
                print(Fore.YELLOW + "=" * shutil.get_terminal_size()[0])

            self.memorize("assistant", response)
            return response
        elif not role == "system":
            raise NotImplementedError
