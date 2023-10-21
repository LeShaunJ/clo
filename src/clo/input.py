#!/usr/bin/env python3
"""Input handler"""

import sys
import os.path
import argparse
import re
import io
import textwrap
import json
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
from .types import URL, Domain, TICK, Env
from .output import Levels, Log
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

###########################################################################


class Parser(argparse.ArgumentParser):

    def exit(self, status: int = 0, message=None):
        if message:
            Log.ERROR(message, code=status)
        raise Log.EXIT(code=status)

    def error(self, message):
        _level = Log.Level
        Log.Bump(Levels.INFO)
        Log.INFO(self.format_usage().strip())
        Log.Level = _level
        self.exit(2, message)


class HelpFormat(argparse.RawDescriptionHelpFormatter):  # pragma: no cover

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

    def format_help(self):
        help = super().format_help()
        return f"\n{help}\n"


class DemoAction(argparse._StoreAction):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, path: Path | str, option_string=None):
        creds = Common.Demo()
        text = "\n".join([f"{Env.at(k)}={json.dumps(v)}" for k, v in creds.items()])

        if not path:
            path = self.default
            print(f'\nSaving demo credentials to {path}\n')

        path = Path(path).resolve()

        with open(path, 'w') as file:
            print(file)
            raise Log.EXIT(text, code=0, file=file)


class Namespace(argparse.Namespace):
    action: Action
    model: Model
    instance: str
    database: str
    username: str
    demo: io.TextIOWrapper
    raw: bool = False
    csv: bool = False
    logging: Levels
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


###########################################################################


class _Explain(type):
    def __init_subclass__(cls) -> None:
        raise TypeError(f'{cls.__name__} class cannot be subclassed.')

    def __getitem__(cls, __name: str):
        try:
            prop: classmethod = object.__getattribute__(cls, __name)
            meth: Callable[[type[cls]], None] = prop.__get__(cls)
            return textwrap.dedent(meth())
        except Exception as e:
            Log.ERROR(e, code=30)


class Explain(metaclass=_Explain):
    """A container for specialize documention. This is called when the user runs `clo explain TOPIC`.
    """

    @classmethod
    def domains(cls) -> str:
        """Outputs information regarding Odoo search domains.
        """
        from .output import Columnize

        operators = [
            ('=, !=, >, >=, <, <=', ("Standard comparison operators.")),
            ('=?', (
                "Unset or equals to (\033[2mreturns true if value is either None or False, otherwise "
                "behaves like `=`\033[0m)."
            )),
            ('=[i]like', (
                """Matches `FIELD` against the value pattern. An underscore (`_`) in the pattern """
                """matches any single character; a percent sign (`%`) matches any string of zero """
                """or more characters. `=ilike` makes the search case-insensitive."""
            )),
            ('[not ][i]like', (
                """Matches (\033[2mor inverse-matches\033[0m) `FIELD` against the %value% pattern. """
                """Similar to `=[i]like` but wraps value with `%` before matching."""
            )),
            ('[not ]in', (
                """Is—or is not—equal to any of the items from value, value should be a list """
                """of items."""
            )),
            ('child_of', (
                """Is a child (\033[2mdescendant\033[2m) of a value record (\033[2mvalue can be either """
                """one item or a list of items\033[0m). Takes the semantics of the model into account """
                """(\033[2mi.e following the relationship `FIELD` named by `VALUE`\033[0m)."""
            )),
            ('parent_of', (
                """Is a child (\033[2mascendant\033[2m) of a value record (\033[2mvalue can be either """
                """one item or a list of items\033[0m). Takes the semantics of the model into account """
                """(\033[2mi.e following the relationship `FIELD` named by `VALUE`\033[0m)."""
            )),
        ]
        attrs = [
            ('`FIELD`:', (
                """A field name of the current model, or a relationship traversal through a """
                """`Many2one` using dot-notation."""
            )),
            ('`OPERATOR`:', (
                "An operand used to compare the `FIELD` with the value. Valid operators are:"
            )),
            ('', operators),
            ('`VALUE`:', (
                """Variable type, must be comparable (through `OPERATOR`) to the named `FIELD`."""
            )),
        ]
        result = Columnize(attrs, 100).rstrip()

        return '\n'.join([
            '',
            '#### DOMAINS',
            '',
            'A domain is a set of criteria, each criterion being a throuple of `(FIELD, OPERATOR, VALUE)` where:',
            '',
            result
        ])

    @classmethod
    def logic(cls) -> str:
        """Outputs information regarding Odoo search domains' logical operators.
        """
        return (
            """
            #### LOGIC

            Domain criteria can be combined using logical operators in prefix form:

                --or -d login = user -d name = "John Smith" -d email = user@domain.com

            is equivalent to `login == "user" || name == "John Smith" || email == "user@domain.com"`

                --not -d login = user` or `-d login '!=' user

            are equivalent to `login != "user"`. `--not` is generally unneeded, save for negating the """
            """OPERATOR, `child_of`, or `parent_of`.

                --and -d login = user -d name = "John Smith"

            is equivalent to `login == "user" && name == "John Smith"`; though, successive domains"""
            """imply `--and`.
            """
        )

    @classmethod
    def models(cls) -> str:
        """Retrieves relevant metadata for all models in the specified Odoo instance/database.

        Returns:
            str: A formatted, human-readable documentation.
        """
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
        return f"#### MODELS\n\nThe following models are available to query:\n\n{text}"

    @classmethod
    def fields(cls) -> str:
        """Retrieves relevant metadata for all models in the specified Odoo instance/database.

        Returns:
            str: A formatted, human-readable documentation.
        """
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
        return f"\n#### FIELDS\n\nThe following fields apply to the `{Settings.model}` model:\n\n{text}"


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
    if Settings.readme:
        return

    path = Path(path_str)
    try:
        path = path.expanduser().resolve(True)
        assert path.exists()
        load_dotenv(dotenv_path=path, interpolate=True)
    except (FileNotFoundError, AssertionError):
        Log.WARN(f"Environment file `{path_str}` was not found.")

    return path


def Ask(
    prompt: str,
    name: str = "ARGUMENT",
    secret: bool = False,
    env: str = None,
    default: str = "",
    kind: type[T] = str,
) -> Callable[[str], T]:
    from getpass import getpass

    enter = getpass if secret else input

    def inner(value: str | None) -> T:
        if Settings.readme:
            return value
        if env is not None:
            value = os.environ.get(env, default)
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
                    stdin = " ".join([*sys.stdin]).strip()
                    assert re.match(match, stdin)
                    setattr(space, attr, [int(i) for i in stdin.split(" ")])
                    return TICK
                except Exception:
                    raise argparse.ArgumentError(f'"{stdin}" is invalid for `{name}`.')

            return int(*args, **kwargs)

    return ID


def GetOpt(argv: list[str]) -> Namespace:
    global Settings
    Settings = Namespace()

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
                    "help": (
                        f"A set of criterion to filter the search by (run `{__prog__} explain domains` for "
                        "details). This option can be specified multiple times."
                    ),
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
                    "help": (
                        f"A logical `OR`, placed before two or more domains (arity 2). Run `{__prog__} explain "
                        "logic` for more details."
                    ),
                    "action": "append_const",
                    "const": "|",
                    "dest": "positional",
                },
            ),
            Argument(
                ["--and", "-a"],
                {
                    "help": (
                        f"A logical `AND` to place before two or more domains (arity 2). Run `{__prog__} "
                        "explain logic` for more details."
                    ),
                    "const": "&",
                    "action": "append_const",
                    "dest": "positional",
                },
            ),
            Argument(
                ["--not", "-n"],
                {
                    "help": (
                        f"A logical `OR` to place before a signle domain (arity 1). Run `{__prog__} explain "
                        "logic` for more details."
                    ),
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
                "help": (
                    "The ID number(s) of the record(s) to perform the action on. Specifying `-` expects a "
                    "space-separated list from STDIN."
                ),
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
                "help": "Attribute(s) to return for each field, all if empty or not provided.",
                "metavar": "NAME",
                "nargs": "+",
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
                'nargs': '?',
                "help": "Generate a demo instance from Odoo Cloud and save the connection properties to `FILE`.",
                "metavar": "FILE",
                "default": Env.CONF.value,
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
                "default": Env.CONF.value,
            },
        )
        Logs = Argument(
            ["--log"],
            {
                "metavar": "LEVEL",
                "action": "store",
                "type": Log.Bump,
                "default": Levels.WARN.name,
                "choices": Levels.names(),
                "dest": "logging",
                "help": f"The level ({Levels.pretty()}) of logs to produce.",
            },
        )

        Prog: Program = {
            "prog": __prog__,
            "description": f"{__title__} - Perform API operations on Odoo instances via the command-line.",
            "usage": "%(prog)s [OPTIONS] ACTION ...",
            "add_help": False,
            "conflict_handler": "resolve",
            "formatter_class": HelpFormat,
            "exit_on_error": False,
            "epilog": textwrap.dedent((
                f"""
                \033[4mREQUISITES\033[0m:

                The following inputs are \033[1mrequired\033[0m, but have multiple or special specifications. In """
                f"""the absense of these inputs, the program will ask for input:

                - `--instance` can be specified using environment variable \033[1m`{Env.INSTANCE}`\033[0m.
                - `--database` can be specified using environment variable \033[1m`{Env.DATABASE}`\033[0m.
                - `--username` can be specified using environment variable \033[1m`{Env.USERNAME}`\033[0m.
                - The `password` (or `API-key`) \033[1mMUST BE\033[0m specified using environment variable """
                f"""\033[1m`{Env.PASSWORD}`\033[0m.

                `clo` also looks for a `{Env.CONF.value}` file in the working directory that contain these values, """
                """or the file specified by `--env FILE`, if it exists.
                """
            )),
        }
        Commands = Sub(
            details={
                "title": "actions",
                "description": (
                    "The Odoo instance is queried, or operated on, using `ACTIONS`. Each `ACTION` has "
                    "it's own set of arguements; run `%(prog)s ACTION --help` for specific details."
                ),
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
                            "usage": (
                                "%(prog)s [[-o|-n|-a] -d FIELD OPERATOR VALUE [-d ...]] [--offset POSITION] "
                                "[--limit AMOUNT] [--order FIELD] [--count] [-h]"
                            ),
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
                            "description": (
                                "Returns the number of records in the current model matching "
                                "the provided domain."
                            )
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
                            "usage": (
                                "%(prog)s [[-o|-n|-a] -d FIELD OPERATOR VALUE [-d ...]] [-f FIELD ...] "
                                "[--offset POSITION] [--limit AMOUNT] [--order FIELD] [--csv [FILE]] [--help]"
                            ),
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
                            "description": (
                                "Retrieves raw details of the fields available in the current model.\n"
                                "For user-friendly formatting, run `%(prog)s explain fields`."
                            )
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

        def Inst():
            return Argument(
                ["--inst", "--instance"],
                {
                    "metavar": "URL",
                    "action": "store",
                    "default": Env.INSTANCE.get(),
                    "type": URL,
                    "dest": "instance",
                    "help": "The address of the Odoo instance. See \033[4mREQUISITES\033[0m below for details.",
                },
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
                cls.Inst(),
                Argument(
                    ["--db", "--database"],
                    {
                        "metavar": "NAME",
                        "action": "store",
                        "default": Env.DATABASE.get(),
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
                        "default": Env.USERNAME.get(),
                        "dest": "username",
                        "help": "The user to perform operations as. See \033[4mREQUISITES\033[0m below for details.",
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

    try:
        # Preprocess Logging arg so that it's available to Common & Model
        try:
            Starters = Parser(**Input.Prog)
            arg_sets = [
                lambda: [Input.Logs, Input.Out],
                lambda: [Input.Demo, Input.ReadMe],
                lambda: [Input.Environ],
                lambda: [Input.Inst()]
            ]
            for arg_set in arg_sets:
                [
                    Starters.add_argument(*inp.names, **inp.details)
                    for inp in arg_set()
                ]
                _, argv = Starters.parse_known_args(argv, namespace=Settings)
        except argparse.ArgumentError:
            pass

        parser = Build(Input.Prog, Input.Globals(), Input.Commands)

        if Settings.readme:
            raise Log.EXIT(GetReadMe(parser), file=Settings.out)

        # Process all args
        try:
            parser.parse_args(argv, Settings)
            Log.DEBUG(Settings)
            return Settings
        except argparse.ArgumentError as e:
            Log.Bump(Levels.INFO)
            Log.INFO(parser.format_usage().strip())
            Log.ERROR(e, code=1)
    except Exception as e:
        Log.ERROR(e, code=2)


def GetReadMe(
    parser: argparse.ArgumentParser,
    /,
    lines: list[str] = [],
    base: int = 0,
) -> str:  # pragma: no cover
    """Recursively generate the README documentation.

    Args:
        parser (argparse.ArgumentParser): A complete ArgumentParser object.
        lines (list[str], optional): For recursing, acts as the container for generated lines.
        base (int, optional): For recursing, increments the heading levels by the value provided.

    Returns:
        str: The completed README string.
    """
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
        text = re.sub(r"\033\[1m([\S\s]+?)\033\[0m", r"**\1**", text)
        text = re.sub(r"\033\[2m([\S\s]+?)\033\[0m", r"\1", text)
        text = re.sub(r"\033\[3m([\S\s]+?)\033\[0m", r"_\1_", text)
        text = re.sub(r"(?<!\]|`)[(]([\S\s]+?)[)]", r"(_\1_)", text)
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
        lines.extend([
            '[![Build Status][build_status_badge]][build_status_link]',
            '[![Coverage][coverage_badge]][coverage_link]',
            '[![PyPI version][pypi_badge]][pypi_link]',
            '',
        ])

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

    if base == 0:
        lines.append(header(3, 'Concepts'))
        lines.extend([
            'The following breakdowns apply to search-style `ACTIONS`.',
            '',
            format(Explain['domains']),
            textwrap.dedent(format(Explain['logic'])),
        ])

        lines.append(header(2, 'See Also'))
        lines.extend([
            '',
            '* [Changelog](https://github.com/LeShaunJ/clo/blob/main/CHANGELOG.md)',
            '* [Contributing](https://github.com/LeShaunJ/clo/blob/main/CONTRIBUTING.md)',
            '* [Code of Conduct](https://github.com/LeShaunJ/clo/blob/main/CODE_OF_CONDUCT.md)',
            '* [Security](https://github.com/LeShaunJ/clo/blob/main/SECURITY.md)',
        ])
        lines.extend([
            '',
            '![Banner][banner]',
            '',
            '[banner]: https://leshaunj.github.io/clo/assets/images/logo-social.png',
            '[build_status_badge]: https://github.com/LeShaunJ/clo/actions/workflows/test.yml/badge.svg',
            '[build_status_link]: https://github.com/LeShaunJ/clo/actions/workflows/test.yml',
            '[coverage_badge]: https://raw.githubusercontent.com/LeShaunJ/clo/main/docs/assets/images/coverage.svg',
            '[coverage_link]: https://raw.githubusercontent.com/LeShaunJ/clo/main/docs/assets/images/coverage.svg',
            '[pypi_badge]: https://badge.fury.io/py/clo.svg',
            '[pypi_link]: https://badge.fury.io/py/clo',
        ])

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
    "Explain",
    "Argument",
    "Command",
    "Program",
    "Ask",
    "StdInArg",
    "GetOpt",
]

###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")  # pragma: no cover
