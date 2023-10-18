import sys
import pytest
import json
import clo
import io
import re
from clo.output import Log
from unittest import mock

def_args = ["--env", ".clorc", "read"]

###########################################################################


@pytest.mark.parametrize("args", [(["--ids", "2"])], ids=["read with one ID"])
def test_ids(args: list[str], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, *args])

    out, err = capsys.readouterr()
    assert e.value.code == 0
    records = json.loads(out)
    assert all([isinstance(r, dict) for r in records])
    print(out, err)


@pytest.mark.parametrize(
    "args,input", [(["--ids", "-"], "2")], ids=["read with ID from STDIN"]
)
def test_stdin(args: list[str], input: str, capsys):
    with mock.patch("src.clo.input.sys.stdin", new=io.StringIO(f'{input}\n')):
        with pytest.raises(Log.EXIT) as e:
            clo.CLI([*def_args, *args])

        out, err = capsys.readouterr()
        assert e.value.code == 0
        records = json.loads(out)
        assert all([isinstance(r, dict) for r in records])
        print(out, err)


@pytest.mark.parametrize(
    "args,fields",
    [
        (["--ids", "2", "-f"], ["login", "name"]),
    ],
    ids=["read with specific fields"],
)
def test_fields(args: list[str], fields: list[str], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, *args, *fields])

    out, err = capsys.readouterr()
    assert e.value.code == 0
    records: list[dict] = json.loads(out)
    fields = sorted(["id", *fields])
    assert all([(sorted(r.keys()) == fields) for r in records])
    print(out, err)


@pytest.mark.parametrize(
    "args,fields",
    [
        (["--ids", "2", "--csv", "-f"], sorted(["login", "name"])),
    ],
    ids=["read with specific fields"],
)
def test_csv(args: list[str], fields: list[str], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, *args, *fields])

    out, err = capsys.readouterr()
    assert e.value.code == 0
    header = ','.join(["id", *fields])
    assert re.match(fr'\A{header}\r\n', out)
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
