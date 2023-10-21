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

__all__ = [
    'ToJSON',
    'ToCSV',
    'FromCSV',
    'Levels',
    'Log',
]

###########################################################################


def ToJSON(obj: Any) -> str:
    """Convert a serializable object into JSON.

    Args:
        obj (Any): Any serializable object.

    Returns:
        str: A JSON-formatted document.
    """

    return json.dumps(obj, indent="  ")


def ToCSV(
    records: list[dict[str, Any]], file: io.TextIOWrapper, sep: str = ","
) -> None:
    """Write a list of records to CSV.

    Args:
        records (list[dict[str, Any]]): A list of records.
        file (io.TextIOWrapper): The stream the output will be saved to.
        sep (str, optional): The column separator.
    """

    import csv

    try:
        writer = csv.DictWriter(file, records[0].keys(), delimiter=sep, strict=True)
        writer.writeheader()
        writer.writerows(records)
    except Exception as e:
        Log.ERROR(e, code=6)


def FromCSV(file: io.TextIOWrapper, sep: str = ",") -> list[dict[str, Any]]:
    """Convert CSV file contents into a list of records.

    Args:
        file (io.TextIOWrapper): The CSV-formatted input file.
        sep (str, optional): The separator used in the file.

    Returns:
        list[dict[str, Any]]: A list of records.
    """

    import csv

    try:
        return [*csv.DictReader(file, delimiter=sep, strict=True)]
    except Exception as e:  # pragma: no cover
        Log.ERROR(e, code=7)

###########################################################################


class Levels(Enum):
    """An enumerator representing log levels.
    """

    OFF = 0
    """Disables all logging."""
    FATAL = 1
    """Logs when an error causes the program to abort."""
    ERROR = 2
    """Logs when the program has a non-fatal error."""
    WARN = 3
    """Logs when the program needs to warn the user of something."""
    INFO = 4
    """Logs general information."""
    DEBUG = 5
    """Logs verbose, debugging infromation."""
    TRACE = 6
    """Logs egregiously verbos infromation."""

    @classmethod
    def names(cls) -> list[str]:
        return [level.name for level in Levels]

    @classmethod
    def pretty(cls) -> list[str]:
        result = "`, `".join(cls.names())
        return f"`{result}`"


class _Log(type):
    """..."""
    import builtins

    _level: Levels = Levels.OFF
    _print = builtins.print

    @property
    def Level(cls) -> Levels:
        """Gets the current loggin level.
        """
        return cls._level

    @Level.setter
    def Level(cls, which: str | Levels) -> None:
        """Sets the current loggin level.
        """
        if isinstance(which, str):
            which = Levels[which]
        ...
        cls._level = which
        Kind = type(cls)
        always_exit = [Levels.FATAL]
        exiters = [Levels.ERROR, *always_exit]

        def PassFactory(level: Levels):
            __code = 10 if level in always_exit else None

            @classmethod
            def __exit(cls: Kind, *args, code: int = __code, **kwargs) -> None:
                if code is not None:  # pragma: no cover
                    raise Log.EXIT(code=code)

            @classmethod
            def __func(cls: Kind, *args, **kwargs) -> None:
                pass

            return __exit if level in always_exit else __func

        def SendFactory(level: Levels):
            __code = 10 if level in always_exit else None

            @classmethod
            def __exit(
                cls: Kind,
                *values: object,
                sep: str | None = " ",
                end: str | None = "\n",
                flush: Literal[False] = False,
                code: int | None = __code,
            ) -> None:
                cls.__send__(level.name, *values, sep=sep, end=end, flush=flush)
                if code is not None:
                    raise Log.EXIT(code=code)

            @classmethod
            def __func(
                cls: Kind,
                *values: object,
                sep: str | None = " ",
                end: str | None = "\n",
                flush: Literal[False] = False,
            ) -> None:
                cls.__send__(level.name, *values, sep=sep, end=end, flush=flush)

            return __exit if level in exiters else __func

        for level in list(Levels):
            if level == Levels.OFF:
                continue
            ...
            Factory = PassFactory if level.value > which.value else SendFactory
            setattr(cls, level.name, Factory(level))

    def __new__(cls, name: str, bases: tuple[type], dct: dict):
        inst = type.__new__(cls, name, bases, dct)
        inst.Level = Levels.ERROR
        return inst

    @classmethod
    def __send__(
        cls,
        level: str,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ) -> None:
        cls._print(
            f"{level:<5} |",
            *values,
            sep=sep,
            end=end,
            file=sys.stderr,
            flush=flush,
        )

    def Bump(cls, which: str | Levels) -> str:
        """Switches the logging level if the current is less than what is specified.

        Args:
            which (str | Levels): The logging level to switch to.
        """

        if isinstance(which, str):
            which = Levels[which.upper()]

        if which.value < cls.Level.value:
            return cls.Level.name

        cls.Level = which
        return cls.Level.name

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
            import os  # pragma: no cover
            os._exit(self.code)  # pragma: no cover


class Log(metaclass=_Log):
    """A singleton class for outputting logs to `stderr`.
    """

    @classmethod
    def FATAL(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: bool = False,
        code: int = 10,
    ) -> None:
        """Output a `FATAL`-level log.

        Args:
            sep (str | None, optional): A string inserted between values.
            end (str | None, optional): A string appended after the last value.
            flush (bool, optional): Whether to forcibly flush the stream.
            code (int, optional): If set, calls for exit with the code specified.
        """

    @classmethod
    def ERROR(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: bool = False,
        code: int = 10,
    ) -> None:
        """Output an `ERROR`-level log.

        Args:
            sep (str | None, optional): A string inserted between values.
            end (str | None, optional): A string appended after the last value.
            flush (bool, optional): Whether to forcibly flush the stream.
            code (int, optional): If set, calls for exit with the code specified.
        """

    @classmethod
    def WARN(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: bool = False,
    ) -> None:
        """Output a `WARN`-level log.

        Args:
            sep (str | None, optional): A string inserted between values.
            end (str | None, optional): A string appended after the last value.
            flush (bool, optional): Whether to forcibly flush the stream.
        """

    @classmethod
    def INFO(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: bool = False,
    ) -> None:
        """Output an `INFO`-level log.

        Args:
            sep (str | None, optional): A string inserted between values.
            end (str | None, optional): A string appended after the last value.
            flush (bool, optional): Whether to forcibly flush the stream.
        """

    @classmethod
    def DEBUG(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: bool = False,
    ) -> None:
        """Output a `DEBUG`-level log.

        Args:
            sep (str | None, optional): A string inserted between values.
            end (str | None, optional): A string appended after the last value.
            flush (bool, optional): Whether to forcibly flush the stream.
        """

    @classmethod
    def TRACE(
        cls,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: bool = False,
    ) -> None:
        """Output a `TRACE`-level log.

        Args:
            sep (str | None, optional): A string inserted between values.
            end (str | None, optional): A string appended after the last value.
            flush (bool, optional): Whether to forcibly flush the stream.
        """


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


###########################################################################

Tracer = TraceMe(sys.stderr)


@contextmanager
def Trace():
    _stdout = sys.stdout
    sys.stdout = Tracer
    try:
        yield
    finally:
        sys.stdout = _stdout


###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")  # pragma: no cover
