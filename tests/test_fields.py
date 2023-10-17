import pytest
import json
import clo
from clo.output import Log

def_args = ["--env", ".clorc", "fields"]

###########################################################################


@pytest.mark.parametrize("_", [([])], ids=["list all fields"])
def test_all(_: list[str], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args])

    out, err = capsys.readouterr()
    assert e.value.code == 0
    assert isinstance(json.loads(out), dict)
    print(out, err)


@pytest.mark.parametrize(
    "fields", [(["type", "name", "string"])], ids=["list all fields"]
)
def test_some(fields: list[str], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, "--attr", *fields])

    out, err = capsys.readouterr()
    assert e.value.code == 0
    records: dict[str, dict] = json.loads(out)
    fields = sorted(fields)
    assert len([r for r in records.values() if sorted(r.keys()) == fields])
    print(out, err)


###########################################################################
