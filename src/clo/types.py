#!/usr/bin/env python3
"""General types"""

import os
import argparse
from enum import Enum
from typing import Literal, TypedDict, NamedTuple, get_args, Any
from collections import UserString
from .meta import __title__

###########################################################################

TICK = "-"

Logic = Literal['&', '|', '!']
"""
Logical operators used with Domains:

- `&`: A logical `AND` to place before two or more domains (arity 2).
- `|`: A logical `OR`, placed before two or more domains (arity 2).
- `!`: A logical `OR` to place before a signle domain (arity 1).
"""

DEF_HOST = "http://localhost:8069"

###########################################################################


class Env(Enum):
    """A collection of possible environment variables.
    """

    CONF = ".clorc"

    INSTANCE = "instance"
    DATABASE = "database"
    USERNAME = "username"
    PASSWORD = "password"

    def __str__(self) -> str:
        return f"CLO_{self.name}"

    def get(self, __default: str | None = None, /) -> str:
        """Retrieve the environment variable value of a member.

        Args:
            __default (str | None, optional): A value to use if none is
                found in the environment.

        Returns:
            str: The environment variable value
        """

        return os.getenv(f"{self}", __default)

    @classmethod
    def at(cls, value: str) -> "Env":
        """Retrieve the member who holds the specified member value.

        Args:
            value (str): The member value to match.

        Returns:
            Env | None: The matching member, if found.
        """

        return next((e for e in cls if e.value == value))


def AskProperty(
    prompt: str = None,
    env: Env = None,
    default: str = "",
    *,
    secret: bool = False,
):
    """A decorator which provides a property that offers multiple methods to acquire
        an attribute.

        In the event none is explicitly set at the time of retrieval:

        1. Via an optional environment vairable, or
        2. Promopting input from the user.

        Args:
            prompt (str, optional): The prompt to use when asking a use ofr input.
                If none is given, a generic prompt is generated.
            env (Env, optional): An environment variable to lookup before prompting.
            default (str, optional): A value to default to if all attempts fail.
            secret (bool, optional): If `True`, the prompt expects secret input.

        Returns:
            AskProperty: A property object.
    """
    import os
    from getpass import getpass

    kind, enter = (Secret, getpass) if secret else (str, input)

    class AskProperty(property):

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

            name = self.fget.__name__
            self.__inner = f'__{name.lower()}'
            self.__kind = self.fget.__annotations__.get('return', kind)

            if prompt:
                self.__prompt = prompt.rstrip()
            else:
                self.__prompt = f'Please provide a value for {name}'

        def __get__(self, __instance: Any, __owner: type | None = None) -> Any:
            attr = getattr(__instance, self.__inner, None)

            if attr in ("", None) and env is not None:
                attr = os.environ.get(f'{env}', default)

            while attr in ("", None):
                attr = enter(f"{self.__prompt}: ")

            setattr(__instance, self.__inner, attr)

            return self.__kind(attr)

    return AskProperty


class Domain(NamedTuple):
    """Criterion to filter the search by.
    """

    field: str
    """The name of the field to match."""
    operator: Literal[
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "=?",
        "=like",
        "like",
        "not like",
        "ilike",
        "not ilike",
        "=ilike",
        "in",
        "not in",
        "child_of",
        "parent_of",
    ]
    """A comparison operator."""
    value: str
    """The value to compare."""

    @classmethod
    def Operators(cls) -> tuple[type, ...]:
        return get_args(cls.__annotations__["operator"])

    @classmethod
    def Domain(cls, value: str) -> str:
        index = getattr(cls, "_index", 1)
        setattr(cls, "_index", index)
        ...
        if index == 3:
            setattr(cls, "_index", 1)
        else:
            if index == 2:
                ops = cls.Operators()
                if value not in ops:
                    pretty_ops = '","'.join(ops)
                    raise argparse.ArgumentTypeError(
                        f""""{value}" is an invalid OPERATOR (valid: "{pretty_ops}")."""
                    )
            ...
            setattr(cls, "_index", index + 1)
        ...
        return value


class Secret(UserString):
    """A string to hold secret values, but obsfucates when printed.
    """

    def __init__(self, seq: object) -> None:
        if seq:
            super().__init__(seq)
        else:
            super().__init__('')

    def __str__(self) -> str:
        return "*" * len(self)

    ...

    def __repr__(self) -> str:
        return f"'{self}'"


class URL(str):
    def __new__(cls, object=...):
        from urllib.parse import urlparse

        txt = str(object)
        ...
        try:
            url = urlparse(txt)
            assert url.scheme and url.netloc
        except AssertionError:
            raise argparse.ArgumentError(None, f'"{txt}" is not a valid instance URL.')
        ...
        return txt


class Credentials(TypedDict):
    instance: str
    database: str
    username: str
    password: str


###########################################################################

__all__ = [
    'Env',
    'AskProperty',
    'Logic',
    'Domain',
    'Secret',
    'URL',
    'Credentials',
]

###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")  # pragma: no cover
