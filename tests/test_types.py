import pytest
import re
import sys
import io
from clo.types import Secret, URL
from clo.output import Log, Levels, ToCSV, FromCSV

def_args = ["--env", ".clorc", "write"]

###########################################################################


@pytest.mark.parametrize(
    "func,pattern",
    [
        ('str', r"^\*+$"),
        ('repr', r"^'\*+'$"),
    ],
    ids=[
        "secret __str__ is obsfucated",
        "secret __repr__ is obsfucated",
    ],
)
def test_secret(func: str, pattern: re.Pattern):
    secret = Secret('password')
    result = getattr(secret, f'__{func}__')
    assert re.match(pattern, result())


def test_url():
    from argparse import ArgumentError
    with pytest.raises(ArgumentError) as a:
        URL('htt&2325jklj')

    assert a.value.message


def test_bump():
    Log.Level = "TRACE"
    Log.Bump("ERROR")
    assert Log.Level == Levels.TRACE


def test_tocsv_fail(capsys):
    with pytest.raises(Log.EXIT) as e:
        ToCSV({5, 6, 7, 8}, sys.stdout)

    _, err = capsys.readouterr()
    assert e.value.code > 0
    assert err


def test_fromcsv_pass():
    fields = ["id", "name", "login", "email"]

    records = FromCSV(io.StringIO('\n'.join([
        ','.join(fields),
        "2,Dirty,dirt,dirt@domain.com",
        "5,Clint,cli,cl@domain.com",
        "7,Dirty,dirt,dirt@domain.com",
        "9,East Wood,e.wood,e.wood@domain.com",
    ])))
    fields = sorted(fields)

    assert len(records) == 4
    assert all([
        sorted(r.keys()) == fields
        for r in records
    ])


def test_common_load(capsys):
    from clo.api import Common
    with pytest.raises(Log.EXIT) as e:
        Common.Load('')

    _, err = capsys.readouterr()
    assert e.value.code > 0
    assert err


def test_dry_run(capsys):
    from clo import CLI
    with pytest.raises(Log.EXIT) as e:
        CLI(["--env", ".clorc", "--dry-run", "search"])

    _, err = capsys.readouterr()
    assert e.value.code == 0
    assert err.startswith("DEBUG | Model['res.users'].Search([], offset=0)")


###########################################################################
