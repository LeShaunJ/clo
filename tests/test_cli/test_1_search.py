import pytest
import clo
import re
from clo.output import Log
from tests.compare import CMP, EQ, GT

def_args = ["--env", ".clorc", "search"]

###########################################################################


@pytest.mark.parametrize(
    "args,pattern,code",
    [
        ([], r"^\[\n( +\d+(,|(?=\n\]))\n)+\]\n$", EQ(0)),
        (["--raw"], r"^(\d+( |$))+\n$", EQ(0)),
        (["--limit", "1"], r"^\[\n +\d+\n\]\n$", EQ(0)),
        (["--offset", "2"], r"^\[\n( +\d+(,|(?=\n\]))\n)+\]\n$", EQ(0)),
        (["--offset", "-1"], None, GT(0)),
        (["-d", "login", "=", "demo"], r"^\[\n +\d+\n\]\n$", EQ(0)),
        (
            ["-n", "-d", "login", "=", "demo"],
            r"^\[\n( +\d+(,|(?=\n\]))\n)+\]\n$",
            EQ(0),
        ),
        (
            ["-o", "-d", "login", "=", "demo", "-d", "login", "=", "admin"],
            r"^\[\n( +\d+(,|(?=\n\]))\n){2}\]\n$",
            EQ(0),
        ),
        (["-d", "login", "=", "dgdfgdfgs"], r"^\[\]\n$", EQ(0)),
        (["-d", "login", "is", "good"], None, GT(0)),
    ],
    ids=[
        "search with no args",
        "search with raw output",
        "search with a limit of 1",
        "search with an offset of 2",
        "search fails with a negative offset",
        "search where login = demo",
        "search where not login = demo",
        "search where login = demo or login = admin",
        "search where nothing matches",
        "search where the operator is invalid",
    ],
)
def test_command(args: list[str], pattern: re.Pattern | None, code: CMP[int], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, *args])

    out, err = capsys.readouterr()
    assert getattr(e.value.code, code.operator, code.value)
    if pattern:
        assert re.match(pattern, out)
    print(out, err)


@pytest.mark.parametrize(
    "arg", ["--help", "-h"], ids=["display help long", "display help short"]
)
def test_help(arg, capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, arg])

    out, err = capsys.readouterr()
    assert out
    assert e.value.code == 0
    print(out, err)


###########################################################################
