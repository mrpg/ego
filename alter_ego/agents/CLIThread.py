from typing import Any
from alter_ego.structure import Thread
from colorama import Fore, Back, init
import shutil

init(autoreset=True)


class CLIThread(Thread):
    """
    Class representing a command-line interface thread.

    This is a type of thread that interacts with the user through the command-line interface.
    Useful for debugging and testing.
    """

    def send(self, role: str, message: str, **kwargs: Any) -> Any:
        """
        Send a message to the thread and possibly receive a response.

        Parameters
        ----------
        role : str
            The role sending the message ("system" or "user").
        message : str
            The message to be sent.
        kwargs : Any
            Additional keyword arguments.

        Returns
        -------
        Any
            The response from the thread, if applicable.

        Raises
        ------
        NotImplementedError
            If the role is not recognized.
        """
        if role == "system":
            print(Back.RED + f"System instructions for {self}:")
            print(message)
            print()
        elif role == "user":
            print(Back.RED + f"Message for {self}:")
            print(message)
            print()

            print(Back.GREEN + f"{self}'s response:")
            response: str = input()

            print(Fore.YELLOW + "=" * shutil.get_terminal_size()[0])

            self.memorize("assistant", response)

            return response
        else:
            raise NotImplementedError

    def cost(self) -> float:
        return 0.0
