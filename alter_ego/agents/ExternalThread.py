from typing import Any, Optional
import alter_ego.structure


class ExternalThread(alter_ego.structure.Thread):
    """
    Class representing a thread that is managed by an external program.
    """

    def send(
        self, role, message: str, response: Optional[Any] = None, **kwargs: Any
    ) -> str:
        if role == "user" and response is not None:
            self.memorize("assistant", response)

            return response
