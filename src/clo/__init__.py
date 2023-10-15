#!/usr/bin/env python3

import sys
import json
from typing import cast
from .meta import __title__, __doc__
from .output import Log, ToCSV
from .api import Common, ProtocolError, Fault
from .input import GetOpt, Namespace, Action, Topic

###########################################################################


def main(argv: list[str] = sys.argv[1:]) -> None:
    try:
        Settings = GetOpt(argv)
        ...
        action = cast(Action, Settings.action).title()
        positional: list = [
            Settings.positional,
            *filter(None, [dict(Settings.keyvalues)]),
        ]
        optional = {
            k: v
            for k, v in vars(Settings).items()
            if k not in Namespace.__annotations__ and v is not None
        }

        if Settings.dry_run:
            Log.Level = Log.Levels.DEBUG
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
            suffix = f" -> {Settings.out.name}"
            suffix += " (CSV)" if Settings.csv else ""
            ...
            Log.DEBUG(f"{repr(Settings.model)}.{action}({args}){suffix}")
            sys.exit(0)

        try:
            Common.Authenticate(
                Settings.database,
                Settings.username,
                Settings.password,
                exit_on_fail=False,
            )
        except LookupError:
            Common.Authenticate(Settings.database, "admin", "admin")
        except ProtocolError as p:
            sys.exit(Common.HandleProtocol(p))
        except Fault as f:
            sys.exit(Common.HandleFault(f))
        except Exception as e:
            Log.FATAL(e, code=5)

        if action == "Explain":
            topic: str = Settings.topic
            Topic[topic]

        Result = getattr(Settings.model, action)(*positional, **optional)
        if Result is None:
            sys.exit(0)

        if Settings.raw and isinstance(Result, list):
            Log.EXIT(" ".join([str(r) for r in Result]), flush=True, file=Settings.out)

        if Settings.csv and isinstance(Result, list):
            ToCSV(Result, Settings.out)
        else:
            Log.EXIT(json.dumps(Result, indent="  "), flush=True, file=Settings.out)
    except KeyboardInterrupt:
        sys.stderr.write("\n")
        Log.FATAL("Operation aborted", flush=True, code=250)


###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")
