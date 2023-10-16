import pytest
import clo

def_args = ["--env", ".clorc", "search"]


def test_noargs(capsys):
    with pytest.raises(SystemExit):
        clo.main([*def_args])
    out, err = capsys.readouterr()
    assert out
    print(out, err)


def test_help(capsys):
    with pytest.raises(SystemExit):
        clo.main([*def_args, "--help"])
    out, err = capsys.readouterr()
    assert out
    with pytest.raises(SystemExit):
        clo.main([*def_args, "-h"])
    out, err = capsys.readouterr()
    assert out
    print(out, err)
