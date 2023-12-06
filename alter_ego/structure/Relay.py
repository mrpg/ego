from typing import Callable, List, Any


class Relay:
    """
    The Relay class serves as a mediator that forwards method calls and attribute settings
    from a source object to multiple target objects.

    :ivar _source: The source object.
    :ivar _targets: A list of target objects.
    """

    def __init__(self, source: Any, targets: List[Any]) -> None:
        """
        Initialize a new Relay instance.

        :param source: The source object.
        :type source: Any
        :param targets: A list of target objects.
        :type targets: List[Any]
        """
        self._source = source
        self._targets = targets

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Overloaded setattr to simultaneously set attributes for source and target objects.

        :param name: The name of the attribute to set.
        :type name: str
        :param value: The value to assign to the attribute.
        :type value: Any
        """
        self.__dict__[name] = value

        if name not in ("_source", "_targets"):
            for target in self._targets:
                setattr(target, name, value)
            setattr(self._source, name, value)

    def call_all(self, methodname: str, *args: Any, **kwargs: Any) -> None:
        """
        Invoke a method on all target objects using provided arguments.

        :param methodname: The method's name to be called on target objects.
        :type methodname: str
        :param args: Positional arguments for the method.
        :type args: Any
        :param kwargs: Keyword arguments for the method.
        :type kwargs: Any
        """
        for target in self._targets:
            getattr(target, methodname)(*args, **kwargs)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Shortcut to call 'save' method on all target objects.

        :param args: Positional arguments for 'save' method.
        :type args: Any
        :param kwargs: Keyword arguments for 'save' method.
        :type kwargs: Any
        """
        self.call_all("save", *args, **kwargs)

    def system(self, *args: Any, **kwargs: Any) -> None:
        """
        Shortcut to call 'system' method on all target objects.

        :param args: Positional arguments for 'system' method.
        :type args: Any
        :param kwargs: Keyword arguments for 'system' method.
        :type kwargs: Any
        """
        self.call_all("system", *args, **kwargs)
