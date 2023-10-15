Contributing
============

All the contributions are welcome! Please open [an issue](https://github.com/LeShaunJ/clo/issues/new) or send us a pull request.

Executing the tests:

```shell
$ pip install -r requirements.txt
$ pip install -e .
$ flake8
$ pytest
```

or with [tox](https://pypi.org/project/tox/) installed:

```shell
$ tox
```


Documentation is published with [mkdocs]():

```shell
$ pip install -r requirements-docs.txt
$ pip install -e .
$ mkdocs serve
```

Open http://127.0.0.1:8000/ to view the documentation locally.
