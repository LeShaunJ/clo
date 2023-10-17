#!/usr/bin/env python3
"""Output handler"""

import sys
import json
import io
from enum import Enum
from typing import Any, TextIO, Literal
from contextlib import contextmanager
from .meta import __title__

###########################################################################


def Pretty(obj) -> str:
    return json.dumps(obj, indent=2)


def ToCSV(
    records: list[dict[str, Any]], file: io.TextIOWrapper, sep: str = ","
) -> None:
    import csv

    try:
        writer = csv.DictWriter(file, records[0].keys(), delimiter=sep, strict=True)
        writer.writeheader()
        writer.writerows(records)
    except Exception as e:
        Log.ERROR(e, code=6)


def FromCSV(file: io.TextIOWrapper, sep: str = ",") -> list[dict[str, Any]]:
    import csv

    try:
        return csv.DictReader(file, delimiter=sep, strict=True)
    except Exception as e:
        Log.ERROR(e, code=7)


###########################################################################


class _Log(type):
    import builtins

    class Levels(Enum):
        OFF = 0
        FATAL = 1
        ERROR = 2
        WARN = 3
        INFO = 4
        DEBUG = 5
        TRACE = 6

        @classmethod
        def names(cls) -> list[str]:
            return [level.name for level in Log.Levels]

        @classmethod
        def pretty(cls) -> list[str]:
            result = "`, `".join(cls.names())
            return f"`{result}`"

    _level: Levels = Levels.OFF
    _print = builtins.print

    @property
    def Level(cls) -> Levels:
        return cls._level

    @Level.setter
    def Level(cls, which: str | Levels) -> None:
        if isinstance(which, str):
            which = cls.Levels[which]
        ...
        cls._level = which
        Kind = type(cls)
        Levels = cls.Levels
        Exiters = [cls.Levels.ERROR, cls.Levels.FATAL]

        def PassFactory(level: Levels):
            @classmethod
            def __exit(cls: Kind, *args, **kwargs) -> None:
                raise Log.EXIT(code=kwargs.get("code", 10))

            @classmethod
            def __func(cls: Kind, *args, **kwargs) -> None:
                pass

            return __exit if level in Exiters else __func

        def SendFactory(level: Levels):
            @classmethod
            def __exit(
                cls: Kind,
                *values: object,
                sep: str | None = " ",
                end: str | None = "\n",
                flush: Literal[False] = False,
                code: int = 10,
            ) -> None:
                cls.__send__(level, *values, sep=sep, end=end, flush=flush)
                raise Log.EXIT(code=code)

            @classmethod
            def __func(
                cls: Kind,
                *values: object,
                sep: str | None = " ",
                end: str | None = "\n",
                flush: Literal[False] = False,
            ) -> None:
                cls.__send__(level, *values, sep=sep, end=end, flush=flush)

            return __exit if level in Exiters else __func

        for level in list(cls.Levels):
            if level == cls.Levels.OFF:
                continue
            ...
            Factory = PassFactory if level.value > which.value else SendFactory
            setattr(cls, level.name, Factory(level))

    def __new__(cls, name: str, bases: tuple[type], dct: dict):
        inst = type.__new__(cls, name, bases, dct)
        inst.Level = cls.Levels.ERROR
        return inst

    @classmethod
    def __send__(
        cls,
        level: Level,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ) -> None:
        cls._print(
            f"{level.name:<5} |",
            *values,
            sep=sep,
            end=end,
            file=sys.stderr,
            flush=flush,
        )

    def Bump(cls, which: str | Levels) -> None:
        if isinstance(which, str):
            which = cls.Levels[which]
        ...
        if which.value < cls._level.value:
            return
        ...
        cls.Level = which

    class EXIT(BaseException):

        def __init__(
            self,
            *values: object,
            code: int = 0,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = True,
            file: io.TextIOWrapper | None = None,
        ) -> None:
            super().__init__(*values)
            self.code = code
            if values:
                print(*values, sep=sep, end=end, file=file, flush=flush)

        def Done(self) -> None:
            import os
            os._exit(self.code)


class Log(metaclass=_Log):
    @classmethod
    def FATAL(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
        code: int = 10,
    ) -> None:
        ...

    @classmethod
    def ERROR(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
        code: int = 10,
    ) -> None:
        ...

    @classmethod
    def WARN(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ) -> None:
        ...

    @classmethod
    def INFO(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ) -> None:
        ...

    @classmethod
    def DEBUG(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ) -> None:
        ...

    @classmethod
    def TRACE(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ) -> None:
        ...


class TraceMe(io.TextIOWrapper):
    def __init__(self, stream: TextIO):
        self.__ = stream
        self.__ended = True

    def write(self, output: Any):
        string = str(output)
        if self.__ended:
            self.__.write("TRACE | ")
            self.__ended = False
        self.__.write(string)

        try:
            self.__ended = string[-1] == "\n"
        except Exception:
            pass

    def flush(self):
        self.__.flush()


###########################################################################

Tracer = TraceMe(sys.stderr)


@contextmanager
def Trace():
    _stdout = sys.stdout
    sys.stdout = Tracer
    yield
    sys.stdout = _stdout


###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")
