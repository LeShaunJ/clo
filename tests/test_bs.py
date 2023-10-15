import pytest
import clo


def test_something(capsys):
    with pytest.raises(SystemExit):
        clo.main(
            [
                "--env",
                ".clorc",
                "search"
            ]
        )
    out, err = capsys.readouterr()
    assert out
    print(out, err)
