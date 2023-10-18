import pytest
import json
import clo
from clo.output import Log

def_args = ["--env", ".clorc", "write"]

###########################################################################


@pytest.mark.parametrize(
    "args",
    [(["--ids", "2", "-v", "name", "Harry", "-v", "email", "hello@world.com"])],
    ids=["write name & login at ID"],
)
def test_command(args: list[str], capsys):
    with pytest.raises(Log.EXIT) as e:
        clo.CLI([*def_args, *args])

    out, err = capsys.readouterr()
    assert e.value.code == 0
    assert json.loads(out) == True  # noqa: E712
    print(out, err)


###########################################################################
