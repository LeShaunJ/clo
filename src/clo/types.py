#!/usr/bin/env python3
"""General types"""

import argparse
from typing import Literal, TypedDict, NamedTuple, get_args
from collections import UserString
from .meta import __title__

###########################################################################

TICK = "-"

###########################################################################


class IR(TypedDict):
    id: int
    model: str
    info: str
    path: list[str]
    children: dict[str, "IR"]


class Secret(UserString):
    ...

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
            raise argparse.ArgumentError(f'"{txt}" is not a valid instance URL.')
        ...
        return txt


class Domain(NamedTuple):
    field: str
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
    value: str

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


class Credentials(TypedDict):
    instance: str
    database: str
    username: str
    password: str


###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")
