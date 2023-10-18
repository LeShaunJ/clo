import sys
import pytest
import clo
from clo.output import Log
from tests.compare import CMP, EQ, GT

def_args = ["--env", ".clorc", "count"]


###########################################################################


@pytest.mark.parametrize(
    "args,cmp,code",
    [
        ([], GT(0), EQ(0)),
        (["--limit", "1"], EQ(2), EQ(0)),
        (["--offset", "2"], EQ(0), EQ(0)),
        (["-d", "login", "=", "demo"], EQ(2), EQ(0)),
        (["-n", "-d", "login", "=", "demo"], GT(1), EQ(0)),
        (
            ["-o", "-d", "login", "=", "demo", "-d", "login", "=", "admin"],
            EQ(2), EQ(0)
        ),
        (["-d", "login", "=", "dgdfgdfgs"], EQ(0), EQ(0)),
    ],
    ids=[
        "count with no args",
        "count with a limit of 1",
        "count with an offset of 2",
        "count where login = demo",
        "count where not login = demo",
        "count where login = demo or login = admin",
        "count where nothing matches",
    ],
)
def test_command(args: list[str], cmp: CMP[int], code: CMP[int], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, *args])

    out, err = capsys.readouterr()
    assert getattr(e.value.code, code.operator, code.value)
    if e.value.code == 0:
        assert getattr(int(out), cmp.operator, cmp.value)
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
    print(out, err, file=sys.__stdout__)


###########################################################################
