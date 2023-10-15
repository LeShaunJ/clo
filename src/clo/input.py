#!/usr/bin/env python3
"""Input handler"""

import sys
import os.path
import argparse
import re
import io
import textwrap
import json
from enum import Enum
from typing import (
    Any,
    Callable,
    Sequence,
    SupportsIndex,
    SupportsInt,
    TypeAlias,
    cast,
    Literal,
    TypeVar,
    TypedDict,
    NamedTuple,
    Optional,
    overload,
)
from .meta import __title__, __prog__, __version__
from .types import URL, Domain, Secret, TICK
from .output import Log
from .api import Common, Model
from pathlib import Path
from dotenv import load_dotenv

###########################################################################

T = TypeVar("T")
Action: TypeAlias = Literal[
    "Search", "Count", "Read", "Find", "Create", "Write", "Delete", "Fields", "Explain"
]
FileType = argparse.FileType
SUPPRESS = argparse.SUPPRESS
DEF_HOST = "http://localhost:8069"

###########################################################################


class Env(Enum):
    CONF = ".clorc"

    INST = "instance"
    DATA = "database"
    USER = "username"
    PASS = "password"

    def __str__(self) -> str:
        return f"OD_{self.name}"

    def get(self, __default: str = "", /) -> str:
        return os.getenv(f"{self}", __default)

    @classmethod
    def at(cls, value: str) -> "Env":
        return next((e for e in cls if e.value == value))


class Parser(argparse.ArgumentParser):
    def exit(self, status: int = 0, message=None):
        if message:
            Log.ERROR(message, code=status)
        sys.exit(status)

    def error(self, message):
        _level = Log.Level
        Log.Bump(Log.Levels.INFO)
        Log.INFO(self.format_usage().strip())
        Log.Level = _level
        self.exit(2, message)


class HelpFormat(argparse.RawDescriptionHelpFormatter):
    ...

    def _get_help_string(self, action):
        help = action.help
        if help is None:
            help = ""

        if "%(default)" not in help:
            if action.default not in [argparse.SUPPRESS, None]:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    if isinstance(action.default, io.TextIOWrapper):
                        help += f" (default: {action.default.name})"
                    else:
                        help += " (default: %(default)s)"
        return help

    ...

    def format_help(self):
        help = super().format_help()
        return f"\n{help}\n"

    ...


class DemoAction(argparse._StoreConstAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **{**kwargs, "const": True})

    def __call__(self, parser, namespace, values, option_string=None):
        creds = Common.Demo()
        [print(f"{Env.at(k)}={json.dumps(v)}") for k, v in creds.items()]
        sys.exit(0)


class Namespace(argparse.Namespace):
    action: Action
    model: Model
    instance: str
    database: str
    username: str
    password: Secret
    demo: bool = False
    raw: bool = False
    csv: bool = False
    logging: Log.Levels
    dry_run: bool
    out: io.TextIOWrapper
    env: Path
    using: io.TextIOWrapper
    readme: bool = False

    positional: list = []
    keyvalues: dict[str, str] = {}

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "action":
            __value = str(__value).title()
        ...
        if __name == "positional" and __value in ([TICK], TICK):
            return
        ...
        return super().__setattr__(__name, __value)


Settings = Namespace()

###########################################################################


class _Topic(type):
    def __getitem__(cls, __name: str):
        try:
            inner: Callable[[type[cls]], None] = object.__getattribute__(cls, __name)
            print(textwrap.dedent(inner()), "\n")
            sys.exit(0)
        except Exception as e:
            Log.ERROR(e, code=30)

    def models(cls) -> str:
        export = sorted([f for f in Model("ir.model").Find()], key=lambda f: f["model"])
        ...
        indent = "  "
        delim = "  "
        pad = max([len(f["model"]) for f in export])
        hang = " " * (len(indent + delim) + pad)
        if Settings.verbose:
            fields = [
                {
                    "model": f'{f["model"]}{delim}'[:pad],
                    "info": f"\n{hang}".join(
                        re.split(r"\n", f"{f['display_name']}{f.get('info','')}"),
                    ).strip(),
                }
                for f in export
            ]
        else:
            fields = [
                {
                    "model": f'{f["model"]}{delim}'[:pad],
                    "info": f["display_name"].strip(),
                }
                for f in export
            ]
        ...
        text = "\n".join(
            [(f'{indent}{f["model"]:{"."}<{pad}}{delim}{f["info"]}') for f in fields]
        )
        ...
        return f"\n\033[4mMODELS\033[0m\n\nThe following models are available to query:\n\n{text}"

    def domains(cls) -> str:
        return """
        \033[4mDOMAINS\033[0m

        A domain is a set of criteria, each criterion being a throuple of (FIELD, OPERATOR, VALUE) where:

        FIELD     A field name of the current model, or a relationship traversal through a `Many2one` using \
            dot-notation.

        OPERATOR  An operator used to compare the FIELD with the value. Valid operators are:

                    =, !=, >, >=, <, <=   Standard comparison operators.
                    =?                    Unset or equals to (returns true if value is either None or False, otherwise \
                        behaves like `=`).
                    =[i]like              Matches FIELD against the value pattern. An underscore ("_") in the pattern \
                        matches any single
                                        character; a percent sign ("%") matches any string of zero or more characters.
                                        `=ilike` makes the search case-insensitive.
                    [not ][i]like         Matches (or inverse-matches) FIELD against the %value% pattern. Similar to \
                        `=[i]like` but wraps value with
                                        "%" before matching.
                    [not ]in              Is—or is not—equal to any of the items from value, value should be a list \
                        of items.
                    child_of              Is a child (descendant) of a value record (value can be either one item or \
                        a list of items). Takes the
                                        semantics of the model into account (i.e following the relationship FIELD \
                                            named by VALUE).
                    parent_of             Is a parent (ascendant) of a value record (value can be either one item or \
                        a list of items). Takes the
                                        semantics of the model into account (i.e following the relationship FIELD \
                                            named by VALUE).

        VALUE     Variable type, must be comparable (through OPERATOR) to the named FIELD.
        """

    def logic(cls) -> str:
        return """
        \033[4mLOGIC\033[0m

          Domain criteria can be combined using logical operators in prefix form:

          `--or -d login = user -d name = "John Smith" -d email = user@domain.com`
            is equivalent to `login == "user" || name == "John Smith" || email == "user@domain.com"`

          `--not -d login = user` or `-d login '!=' user`
            are equivalent to `login != "user"`. `--not` is generally unneeded, save for negating the \
                OPERATOR, `child_of`, or `parent_of`.

          `--and -d login = user -d name = "John Smith"`
            is equivalent to `login == "user" && name == "John Smith"`; though, successive domains \
                imply `--and`.
        """

    def fields(cls) -> str:
        export = [f for f in Settings.model.Fields().values() if f["exportable"]]
        indent = "  "
        delim = "  "
        pad = max([len(f["name"]) for f in export])
        hang = " " * (len(indent + delim) + pad)
        fields = [
            {
                "name": f'{f["name"]}{delim}'[:pad],
                "help": f"\n{hang}".join(
                    [
                        f"{f['string'].strip()}  <{f['type']}>",
                        *re.split(r"\n| {3, }", f.get("help", "")),
                    ]
                ).strip(),
            }
            for f in export
        ]
        text = "\n".join(
            [(f'{indent}{f["name"]:{"."}<{pad}}{delim}{f["help"]}') for f in fields]
        )
        ...
        return f"\n\033[4mFIELDS\033[0m\n\nThe following fields apply to the `{Settings.model}` model:\n\n{text}"


class Topic(metaclass=_Topic):
    ...


###########################################################################


class ToC:
    class Item(NamedTuple):
        title: str
        level: int = 1

    __all: list[Item] = []

    @classmethod
    def Add(cls, title: str, level: int = 1):
        item = cls.Item(title, level - 0)
        cls.__all.append(item)

    @classmethod
    def Format(cls, min_level: int = 2, max_level: int = 4) -> str:
        indent = "  "
        return "\n".join(
            [
                f"{(indent*(a.level-min_level))}* {cls.Link(a.title)}"
                for a in cls.__all
                if a.level >= min_level and a.level <= max_level
            ]
        )

    @staticmethod
    def Link(title: str) -> str:
        href = re.sub(r"\W+", r"-", title.lower())
        return f"[{title}](#{href})"


class Argument(NamedTuple):
    class Detail(TypedDict):
        action: Optional[
            Literal[
                "store",
                "store_const",
                "store_true",
                "append",
                "append",
                "count",
                "help",
                "version",
            ]
        ]
        nargs: Optional[int | Literal["?", "*", "+"]]
        const: Optional[Any]
        default: Optional[str]
        type: Optional[type[int | float | argparse.FileType] | Callable[[str], None]]
        choices: list[str | int]
        required: Optional[bool]
        help: Optional[str]
        metavar: Optional[str | tuple[str]]
        dest: Optional[str]
        version: Optional[str]

    class Exclusive(NamedTuple):
        required: Optional[bool] = False

    class Group(NamedTuple):
        title: Optional[str] = None
        description: Optional[str] = None

    names: list[str]
    details: Detail = {}
    exclusive: Exclusive = None
    group: Group = None


class Command(NamedTuple):
    class Detail(TypedDict):
        help: Optional[str]
        aliases: Sequence[str]
        usage: Optional[str]
        description: Optional[str]
        epilog: Optional[str]
        add_help: Optional[bool]

    name: str
    details: Detail = {}


class Sub(NamedTuple):
    details: Argument = {}
    commands: list[tuple[Command, list[Argument]]] = []
    help: Argument = None


class Program(TypedDict):
    prog: Optional[str]
    description: Optional[str]
    usage: Optional[str]
    add_help: Optional[bool]
    epilog: Optional[str]
    conflict_handler: Optional[Literal["error", "resolve"]]
    formatter_class: Optional[argparse.HelpFormatter]
    exit_on_error: Optional[bool]


###########################################################################


def RC(path_str: str):
    path = Path(path_str)
    if not Settings.demo and path.exists():
        load_dotenv(dotenv_path=path, interpolate=True)
    else:
        Log.WARN(f"Congig file {path} was not found.")
    return path


def Ask(
    prompt: str,
    name: str = "ARGUMENT",
    secret: bool = False,
    env: str = None,
    kind: type[T] = str,
) -> Callable[[str], T]:
    from getpass import getpass

    enter = getpass if secret else input

    def inner(value: str | None) -> T:
        if env is not None:
            value = os.environ.get(env, "")
        while value == "":
            value = enter(f"{prompt}: ")
        return kind(value)

    inner.__name__ = name
    return inner


def StdInArg(
    name: str, space: argparse.Namespace, attr: str, match: re.Pattern = r"^.*$"
):
    class ID:
        @overload
        def __new__(cls, __x: str | SupportsInt | SupportsIndex = ..., /):
            ...

        @overload
        def __new__(cls, __x: str | bytes | bytearray, /, base: SupportsIndex):
            ...

        def __new__(cls, *args, **kwargs):
            if args[0] == TICK:
                try:
                    assert not sys.stdin.isatty()
                    stdin = " ".join([*sys.stdin]).strip()
                    assert re.match(match, stdin)
                    setattr(space, attr, [int(i) for i in stdin.split(" ")])
                    return TICK
                except Exception:
                    raise argparse.ArgumentError(f'"{stdin}" is invalid for `{name}`.')
            return int(*args, **kwargs)

    return ID


def GetOpt(argv: list[str]) -> Namespace:

    def Attach(
        parser: argparse.ArgumentParser,
        arguments: list[Argument] = [],
        help: Argument = None,
    ):
        ...
        exclusives: dict[Argument.Exclusive, argparse._ArgumentGroup] = {}
        groups: dict[Argument.Group, argparse._ArgumentGroup] = {}
        ...
        for argument in filter(None, [*arguments, help]):
            ...
            if argument.group:
                group = argument.group
                if group not in groups:
                    groups[group] = parser.add_argument_group()
                parser = groups[group]
            ...
            if argument.exclusive:
                exclusive = argument.exclusive
                if exclusive not in exclusives:
                    exclusives[exclusive] = parser.add_mutually_exclusive_group(
                        **exclusive
                    )
                parser = exclusives[exclusive]
            ...
            parser.add_argument(*argument.names, **argument.details)

    def Build(
        program: Program, arguments: list[Argument] = [], subs: Sub = None
    ) -> argparse.ArgumentParser:
        parser = Parser(**program)
        if subs:
            sub_parser = parser.add_subparsers(**subs.details)
            ...
            for command, cmd_arguments in subs.commands:
                cmd_parser = cast(
                    Parser,
                    sub_parser.add_parser(
                        command.name,
                        help=command.details.get(
                            "help", command.details.get("description", None)
                        ),
                        add_help=False,
                        formatter_class=program.get("formatter_class", None),
                        exit_on_error=program.get("exit_on_error", True),
                        **command.details,
                    ),
                )
                ...
                Attach(cmd_parser, cmd_arguments, subs.help)
        ...
        Attach(parser, arguments)
        ...
        return parser

    class Input:
        Search: list[Argument] = [
            Argument(
                ["--offset"],
                {
                    "type": int,
                    "help": "Number of results to ignore.",
                    "default": 0,
                    "metavar": "POSITION",
                },
            ),
            Argument(
                ["--limit"],
                {
                    "type": int,
                    "help": "Maximum number of records to return.",
                    "metavar": "AMOUNT",
                },
            ),
            Argument(
                ["--order"],
                {
                    "type": str,
                    "help": "The field to sort the records by.",
                    "metavar": "FIELD",
                },
            ),
        ]
        CSV = Argument(
            ["--csv"],
            {
                "action": "store_true",
                "help": "If `True`, outputs records in CSV format.",
            },
        )
        Domains: list[Argument] = [
            Argument(
                ["--domain", "-d"],
                {
                    "help": f"A set of criterion to filter the search by (run `{__prog__} explain domains` for \
                        details). This option can be specified multiple times.",
                    "nargs": 3,
                    "action": "append",
                    "metavar": ("FIELD", "OPERATOR", "VALUE"),
                    "type": Domain.Domain,
                    "default": [],
                    "dest": "positional",
                },
            ),
            Argument(
                ["--or", "-o"],
                {
                    "help": f"A logical `OR`, placed before two or more domains (arity 2). Run `{__prog__} explain \
                        logic` for more details.",
                    "action": "append_const",
                    "const": "|",
                    "dest": "positional",
                },
            ),
            Argument(
                ["--and", "-a"],
                {
                    "help": f"A logical `AND` to place before two or more domains (arity 2). Run `{__prog__} explain \
                        logic` for more details.",
                    "const": "&",
                    "action": "append_const",
                    "dest": "positional",
                },
            ),
            Argument(
                ["--not", "-n"],
                {
                    "help": f"A logical `OR` to place before a signle domain (arity 1). Run `{__prog__} explain \
                        logic` for more details.",
                    "action": "append_const",
                    "const": "!",
                    "dest": "positional",
                },
            ),
        ]
        Using = Argument(
            ["using"],
            {
                "type": argparse.FileType("r"),
                "help": "A JSON or CSV file of records. ",
                "metavar": "FILE",
            },
        )
        IDs = Argument(
            ["--ids", "-i"],
            {
                "help": 'The ID number(s) of the record(s) to perform the action on. Specifying "-" expects a \
                    speace-separated list from STDIN.',
                "metavar": "ID",
                "nargs": "+",
                "type": StdInArg("--ids", Settings, "positional", r"^[\d ]+$"),
                "required": True,
                "dest": "positional",
            },
        )
        Field = Argument(
            ["--fields", "-f"],
            {
                "help": "Field names to return (default is all fields).",
                "metavar": "FIELD",
                "nargs": "+",
                "default": [],
            },
        )
        Value = Argument(
            ["--value", "-v"],
            {
                "help": "Key/value pair(s) that correspond to the field and assigment to be made, respectively.",
                "metavar": ("FIELD", "VALUE"),
                "action": "append",
                "nargs": 2,
                "dest": "keyvalues",
                "required": True,
            },
        )
        Attr = Argument(
            ["--attributes", "--attr", "-a"],
            {
                "help": "Attribute(s) to return for each field, all if empty or not provided",
                "metavar": "NAME",
                "nargs": "+",
            },
        )
        Inst = Argument(
            ["--inst", "--instance"],
            {
                "metavar": "URL",
                "action": "store",
                "default": Env.INST.get(DEF_HOST),
                "type": Ask(
                    "Enter the Instance URL", "instance", env=f"{Env.INST}", kind=URL
                ),
                "dest": "instance",
                "help": "The address of the Odoo instance. See \033[4mREQUISITES\033[0m below for details.",
            },
        )
        Help = Argument(
            ["--help", "-h"],
            {"action": "help", "help": "Show this help message and exit."},
        )
        ReadMe = Argument(
            ["--readme"],
            {
                "action": "store_true",
                "help": argparse.SUPPRESS,
            },
        )
        Demo = Argument(
            ["--demo"],
            {
                "action": DemoAction,
                "help": "Generate and use a demo instance from Odoo Cloud.",
            },
        )
        Out = Argument(
            ["--out"],
            {
                "type": argparse.FileType("w"),
                "help": "Where to stream the output.",
                "metavar": "FILE",
                "default": sys.stdout,
            },
        )
        Environ = Argument(
            ["--env"],
            {
                "type": RC,
                "help": f"Path to a `{Env.CONF.value}` file. See \033[4mREQUISITES\033[0m below for details.",
                "metavar": "FILE",
                "default": f'{os.getenv("HOME","~")}/{Env.CONF.value}',
            },
        )
        Logs = Argument(
            ["--log"],
            {
                "metavar": "LEVEL",
                "action": "store",
                "default": Log.Levels.ERROR.name,
                "choices": Log.Levels.names(),
                "dest": "logging",
                "help": f"The level ({Log.Levels.pretty()}) of logs to produce.",
            },
        )

        Prog: Program = {
            "prog": __prog__,
            "description": f"{__title__} - Perform API operations on Odoo instances via the command-line.",
            "add_help": False,
            "conflict_handler": "resolve",
            "formatter_class": HelpFormat,
            "exit_on_error": False,
            "epilog": textwrap.dedent(
                f"""
                \033[4mREQUISITES\033[0m:

                The following inputs are \033[1mrequired\033[0m, but have multiple or special specifications. In \
                    the absense of these inputs, the program will ask for input:

                  - `--instance` can be specified using environment variable \033[1m`{Env.INST}`\033[0m.
                  - `--database` can be specified using environment variable \033[1m`{Env.DATA}`\033[0m.
                  - `--username` can be specified using environment variable \033[1m`{Env.USER}`\033[0m.
                  - The `password` (or `API-key`) \033[1mMUST BE\033[0m specified using environment variable \
                    \033[1m`{Env.PASS}`\033[0m.
                """
            ),
        }
        Commands = Sub(
            details={
                "title": "actions",
                "description": "The Odoo instance is queried, or operated on, using `ACTIONS`. Each `ACTION` has it's \
                    own set of arguements; run `%(prog)s ACTION --help` for specific details.",
                "help": "One of the following operations to query, or perform, via the API:",
                "dest": "action",
                "metavar": "ACTION",
                "required": True,
            },
            commands=[
                (
                    Command(
                        "search",
                        {
                            "description": "Searches for record IDs based on the search domain.",
                            "usage": "%(prog)s [[-o|-n|-a] -d FIELD OPERATOR VALUE [-d ...]] [--offset POSITION] \
                                [--limit AMOUNT] [--order FIELD] [--count] [-h]",
                        },
                    ),
                    [
                        *Domains,
                        *Search,
                        Argument(
                            ["--raw", "-r"],
                            {
                                "action": "store_true",
                                "default": False,
                                "help": "Format output as space-separated IDs rather than pretty JSON.",
                            },
                        ),
                    ],
                ),
                (
                    Command(
                        "count",
                        {
                            "description": "Returns the number of records in the current model matching the provided \
                                domain."
                        },
                    ),
                    [*Domains, Search[1]],
                ),
                (
                    Command(
                        "read",
                        {
                            "description": "Retrieves the details for the records at the ID(s) specified."
                        },
                    ),
                    [IDs, Field, CSV],
                ),
                (
                    Command(
                        "find",
                        {
                            "description": "A shortcut that combines `search` and `read` into one execution.",
                            "usage": "%(prog)s [[-o|-n|-a] -d FIELD OPERATOR VALUE [-d ...]] [-f FIELD ...] \
                                [--offset POSITION] [--limit AMOUNT] [--order FIELD] [--csv [FILE]] [--help]",
                        },
                    ),
                    [*Domains, Field, *Search, CSV],
                ),
                (
                    Command(
                        "create",
                        {"description": "Creates new records in the current model."},
                    ),
                    [Value],
                ),
                (
                    Command(
                        "write",
                        {
                            "description": "Updates existing records in the current model."
                        },
                    ),
                    [IDs, Value],
                ),
                (
                    Command(
                        "delete",
                        {"description": "Deletes the records from the current model."},
                    ),
                    [IDs],
                ),
                (
                    Command(
                        "fields",
                        {
                            "description": "Retrieves raw details of the fields available in the current model.\nFor \
                                user-friendly formatting, run `%(prog)s explain fields`."
                        },
                    ),
                    [Attr],
                ),
                (
                    Command(
                        "explain",
                        {"description": "Display documentation on a specified topic."},
                    ),
                    [
                        Argument(
                            ["topic"],
                            {
                                "help": "A topic to get further explanation on.",
                                "choices": ["models", "domains", "logic", "fields"],
                            },
                        ),
                        Argument(
                            ["--verbose", "-v"],
                            {
                                "help": "Display more details.",
                                "action": "store_true",
                                "default": False,
                            },
                        ),
                    ],
                ),
            ],
            help=Help,
        )

        @classmethod
        def Globals(cls) -> list[Argument]:
            return [
                Argument(
                    ["--model", "-m"],
                    {
                        "metavar": "MODEL",
                        "action": "store",
                        "default": "res.users",
                        "type": Model,
                        "help": "The Odoo model to perform an action on. Run `%(prog)s explain models [-v]` to list \
                            available options.",
                    },
                ),
                cls.Environ,
                cls.Inst,
                Argument(
                    ["--db", "--database"],
                    {
                        "metavar": "NAME",
                        "action": "store",
                        "default": Env.DATA.get(),
                        "type": Ask(
                            "Enter the Database Name", "database", env=f"{Env.DATA}"
                        ),
                        "dest": "database",
                        "help": "The application database to perform operations on. See \033[4mREQUISITES\033[0m below \
                            for details.",
                    },
                ),
                Argument(
                    ["--user"],
                    {
                        "metavar": "NAME",
                        "action": "store",
                        "default": Env.USER.get(),
                        "type": Ask(
                            "Enter your Username", "username", env=f"{Env.USER}"
                        ),
                        "dest": "username",
                        "help": "The user to perform operations as. See \033[4mREQUISITES\033[0m below for details.",
                    },
                ),
                Argument(
                    ["--pass"],
                    {
                        "metavar": "SECRET",
                        "action": "store",
                        "default": Secret(Env.PASS.get()),
                        "type": Ask(
                            "Enter your Password (or API-Key)",
                            "password",
                            True,
                            f"{Env.PASS}",
                            Secret,
                        ),
                        "dest": "password",
                        "help": argparse.SUPPRESS,
                    },
                ),
                cls.Demo,
                cls.Out,
                cls.Logs,
                Argument(
                    ["--dry-run"],
                    {
                        "action": "store_true",
                        "help": 'Perform a "practice" run of the action; implies `--log=DEBUG`.',
                    },
                ),
                cls.Help,
                Argument(
                    ["--version"],
                    {
                        "action": "version",
                        "help": "Show version of this program.",
                        "version": f"%(prog)s {__version__}",
                    },
                ),
                cls.ReadMe,
            ]

    # Preprocess Logging arg so that it's available to Common & Model
    try:
        Starter = Parser(**Input.Prog)
        [
            Starter.add_argument(*inp.names, **inp.details)
            for inp in [Input.Logs, Input.Environ, Input.Inst, Input.Out, Input.ReadMe]
        ]
        _, argv = Starter.parse_known_args(argv, namespace=Settings)
        ...
        Log.Level = Log.Levels[Settings.logging]
    except argparse.ArgumentError:
        pass

    parser = Build(Input.Prog, Input.Globals(), Input.Commands)

    if Settings.readme:
        Log.EXIT(GetReadMe(parser), file=Settings.out)

    # Load the proxy
    Common.Load(Settings.instance)

    # Process all args
    try:
        parser.parse_args(argv, Settings)
        Log.DEBUG(Settings)
        return Settings
    except argparse.ArgumentError as e:
        Log.Bump(Log.Levels.INFO)
        Log.INFO(parser.format_usage().strip())
        Log.ERROR(e, code=1)


def GetReadMe(
    parser: argparse.ArgumentParser,
    /,
    lines: list[str] = [],
    toc: ToC = None,
    base: int = 0,
) -> str:
    from argparse import _SubParsersAction

    def header(level: int, text: str, toc: bool = True) -> str:
        level += base
        format = "#" * level
        if toc:
            ToC.Add(text, level)
        return f"{format} {text}\n"

    def setrow(*columns: str):
        columns = [c.replace("|", "\\|") for c in columns]
        lines.append(f'| {" | ".join(columns)} |')

    def headrow(*columns: tuple[str, Literal["L", "C", "R"]]):
        dirs = {"L": ":---", "C": ":--:", "R": "---:"}
        names = [c[0] for c in columns]
        align = [dirs[c[1]] for c in columns]
        [setrow(*c) for c in [names, align]]

    def textrow(arg: argparse.Action, *columns: str):
        if arg.help != argparse.SUPPRESS:
            setrow(*columns)

    def format(text: str) -> str:
        text = re.sub(
            r"\033\[4m(.+?)\033\[0m",
            lambda m: f"[{m.group(1).title()}](#{m.group(1).lower()})",
            text,
        )
        text = re.sub(r"\033\[1m(.+?)\033\[0m", r"**\1**", text)
        text = re.sub(r"\033\[3m(.+?)\033\[0m", r"_\1_", text)
        return text

    def requisite(arg: argparse.Action) -> Literal["YES", "NO"]:
        return "YES" if arg.required else "NO"

    def defaulter(arg: argparse.Action):
        try:
            assert arg.default is not None
            assert arg.default != argparse.SUPPRESS
            return f"`{json.dumps(arg.default)}`"
        except Exception:
            return ""

    def name(arg: argparse.Action) -> str:
        if arg.metavar:
            return f"`{arg.metavar}`"
        elif arg.choices:
            return f'`{{{",".join(arg.choices)}}}`'

    def flags(arg: argparse.Action) -> str:
        result = re.sub(r"-", "\u2011", "`<br>`".join(arg.option_strings))
        return f"`{result}`"

    def meta(arg: argparse.Action) -> str:
        try:
            assert arg.metavar
            metavar = arg.metavar
            if isinstance(metavar, tuple):
                metavar = "`<br>`".join(metavar)
            return f"`{metavar}`"
        except Exception:
            return ""

    def help(arg: argparse.Action) -> str:
        result = ""
        try:
            assert arg.help
            assert arg.help != argparse.SUPPRESS
            result = format(arg.help % {"prog": parser.prog, "default": arg.default})
        except Exception:
            pass
        finally:
            return result

    tocpl = "%(ToC)s"
    tmpv = {"prog": parser.prog}
    usage = re.sub(r"^usage: ", r"", parser.format_usage().strip())
    usage = f"```sh\n{usage}\n```\n"
    args = [a for a in parser._actions if not isinstance(a, _SubParsersAction)]

    if base == 0:
        lines.append(header(1, __title__))

        descr = re.sub(rf"^{re.escape(__title__)} - ", r"", parser.description.strip())
        lines.append(f"{descr % tmpv}\n")

        lines.append(header(2, "Contents", False))
        lines.append(f"{tocpl}\n")

        lines.append(header(2, "Installation"))
        lines.append(f"```sh\npip3 install {parser.prog}\n```\n")

        lines.append(header(2, "Usage"))
        lines.append(usage)

        if args:
            lines.append(header(3, "Globals"))
            lines.append("The following parameters apply to any [Action](#actions).\n")
        arg_lvl = 4
    else:
        lines.append(usage)
        lines.append(f"{parser.description % tmpv}\n")
        arg_lvl = 2

    nbsp = "\u00A0"
    head_descr = f'{"Description":{nbsp}<{(28*3)}}.'

    pos = [p for p in args if not p.option_strings]
    if pos:
        lines.append(header(arg_lvl, "Positional"))
        headrow(
            ("Argument", "L"), ("Required", "C"), (head_descr, "L"), ("Default", "L")
        )
        [
            textrow(arg, name(arg), requisite(arg), help(arg), defaulter(arg))
            for arg in pos
        ]
        lines.append("")

    opts = [o for o in args if o.option_strings]
    if opts:
        lines.append(header(arg_lvl, "Options"))
        headrow(
            ("Flag(s)", "L"),
            ("Argument", "C"),
            ("Required", "C"),
            (head_descr, "L"),
            ("Default", "L"),
        )
        [
            textrow(
                arg, flags(arg), meta(arg), requisite(arg), help(arg), defaulter(arg)
            )
            for arg in opts
        ]
        lines.append("")

    if parser.epilog:
        epilog = parser.epilog.strip()
        epilog = re.sub(
            r"^\033\[4m(.+?)\033\[0m:",
            lambda m: header(arg_lvl, m.group(1).title()),
            epilog,
            flags=re.M,
        )
        epilog = re.sub(r"^", r"> ", epilog, flags=re.M)
        lines.append(format(epilog))

    sub = parser._subparsers
    if sub:
        lines.append(header(3, sub.title.title()))
        lines.append(f"{sub.description % tmpv}\n")

        cmds: dict[str, Parser] = sub._group_actions[0].choices
        for title, command in cmds.items():
            lines.append(header(4, title.title()))
            GetReadMe(command, lines=lines, base=base + 3)

    doc = "\n".join(lines)
    if tocpl in doc:
        doc = doc.replace(tocpl, ToC.Format())

    return doc


###########################################################################

__all__ = [
    "Action",
    "Env",
    "Parser",
    "HelpFormat",
    "Settings",
    "Topic",
    "Argument",
    "Command",
    "Program",
    "Ask",
    "StdInArg",
    "GetOpt",
]

###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")
