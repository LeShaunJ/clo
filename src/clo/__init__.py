#!/usr/bin/env python3
"""The main entry-point for `clo`.
"""

from .meta import __title__, __doc__
from . import api, input, output, types

__all__ = [
    'api',
    'input',
    'output',
    'types',
    'CLI',
    'Main'
]

###########################################################################


def CLI(argv: list[str] = None) -> None:
    """Run `clo` as one would in the shell.

    Args:
        argv (list[str], optional): A list of arguments to pass to the CLI; otherwise,
            `sys.argv[1:]` is used.

    Raises:
        Log.EXIT: Raised when the CLI is done it's job and poised to exit.
    """
    import sys
    from typing import cast
    from .output import Levels, Log, ToCSV, ToJSON
    from .api import Common, ProtocolError, Fault
    from .input import GetOpt, Namespace, Action, Explain

    try:
        Settings = GetOpt(argv if argv else sys.argv[1:])
        ...
        action = cast(Action, Settings.action).title()
        positional: list = [
            Settings.positional,
            *filter(None, [dict(Settings.keyvalues)]),
        ]
        optional = {
            k: v
            for k, v in vars(Settings).items()
            if k not in Namespace.__annotations__
            and v is not None
        }

        # Initialize Common
        Common(
            Settings.instance,
            Settings.database,
            Settings.username,
        )

        if Settings.dry_run:
            Log.Level = Levels.DEBUG
            args = ", ".join(
                filter(
                    None,
                    [
                        *[f"{p}" for p in positional],
                        *[f"{k}={v}" for k, v in optional.items()],
                    ],
                )
            )
            ...
            try:
                suffix = f" -> {Settings.out.name}"
            except AttributeError:
                suffix = " -> ???"
            suffix += " (CSV)" if Settings.csv else ""
            ...
            Log.DEBUG(repr(Common))
            Log.DEBUG(f"{repr(Settings.model)}.{action}({args}){suffix}")
            raise Log.EXIT()

        if action == "Explain":
            topic: str = Settings.topic
            raise Log.EXIT(Explain[topic], "\n")
        elif action in ['Create']:
            Result = getattr(Settings.model, action)(*filter(None, positional))
        elif action in ['Fields']:
            Result = getattr(Settings.model, action)(**optional)
        else:
            Result = getattr(Settings.model, action)(*positional, **optional)

        if Result is None:
            raise Log.EXIT()

        if Settings.raw and isinstance(Result, list):
            raise Log.EXIT(" ".join([str(r) for r in Result]), flush=True, file=Settings.out)

        if Settings.csv and isinstance(Result, list):
            ToCSV(Result, Settings.out)
            raise Log.EXIT(code=0)
        else:
            raise Log.EXIT(ToJSON(Result), flush=True, file=Settings.out)
    except ProtocolError as p:
        raise Log.EXIT(code=Common.HandleProtocol(p))
    except Fault as f:
        raise Log.EXIT(code=Common.HandleFault(f))
    except Exception as e:
        Log.FATAL(e, code=5)
    except KeyboardInterrupt:
        sys.stderr.write("\n")
        Log.FATAL("Operation aborted", flush=True, code=250)


def Main(argv: list[str] = None) -> None:
    from .output import Log
    try:
        CLI(argv)
    except Log.EXIT as e:
        e.Done()


###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")
