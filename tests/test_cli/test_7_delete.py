import pytest
import json
import clo
from clo.output import Log

env_args = ["--env", ".clorc"]
def_args = [*env_args, "delete"]

###########################################################################


@pytest.mark.parametrize("_", [tuple()], ids=["delete record at ID"])
def test_command(_: list[str], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*env_args, "search"])

    out, err = capsys.readouterr()
    ids: list[int] = sorted(json.loads(out))

    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, "--ids", str(ids[-1])])

    out, err = capsys.readouterr()
    assert e.value.code == 0
    assert json.loads(out) == True  # noqa: E712
    print(out, err)


###########################################################################
