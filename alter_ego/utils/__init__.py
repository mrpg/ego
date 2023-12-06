import html
import re
from typing import Any, Optional, Union, List


def from_file(file_name: str) -> str:
    """
    Read file content as a stripped string.

    :param str file_name: The name of the file to read.
    :return: The content of the file as a stripped string.
    :rtype: str
    """
    with open(file_name) as f:
        return f.read().strip()


def extract_number(s: str) -> Optional[Union[int, float]]:
    """
    Extract a single number, potentially a float, from a string.

    This function uses a straightforward definition of "number" that excludes
    scientific notation like 3e8.

    :param str s: The string to extract the number from.
    :return: The extracted number as an integer or a float, if applicable. Returns None otherwise.
    :rtype: Optional[Union[int, float]]
    """
    pattern = r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?"
    matches = re.findall(pattern, s)

    if len(matches) == 1:
        match = matches[0]
        return (
            float(match)
            if ("." in match and float(match) != int(match))
            else int(match)
        )
    else:
        return None


def exclusive_response(
    s: str,
    tokens: List[str],
    *,
    case_insensitive: bool = True,
) -> Optional[str]:
    """
    Validates that a string contains only one of a list of tokens.

    :param str s: The string to search in.
    :param List[str] tokens: List of allowable tokens.
    :param bool case_insensitive: If True, the function will be case insensitive.
    :return: The first matching token found, or None.
    :rtype: Optional[str]
    """
    which = None
    s2 = s.lower() if case_insensitive else s

    for needle in tokens:
        needle2 = needle.lower() if case_insensitive else needle

        if which is None:
            if needle2 in s2:
                which = needle
        else:
            if needle2 in s2:
                raise RuntimeError(f"Response contains '{which}' and '{needle}'.")

    return which


def homogenize(s: str) -> str:
    # TODO: doc

    s = s.replace("\r", "\n")

    s = "\n".join(r.strip() for r in s.split("\n"))

    while "  " in s or "\n\n\n" in s:
        s = s.replace("  ", " ").replace("\n\n\n", "\n\n")

    return s.strip()


def to_html(s: str) -> str:
    """
    Escapes special characters and converts newlines to HTML format.

    :param str s: The string to convert.
    :return: The converted string in HTML format.
    :rtype: str
    """
    s = html.escape(s)
    s = s.replace("\n", "<br>")
    return s
