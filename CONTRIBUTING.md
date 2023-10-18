Contributing
============

Contributions are welcome; just open [an issue](https://github.com/LeShaunJ/clo/issues/new) or send us a pull request.

## Testing

Executing the test in your environment:

```shell
pip install -r requirements.txt
pip install -e .
flake8
pytest
```

or with [tox](https://pypi.org/project/tox) installed:

```shell
tox
```

## Documenting

Docs published using [mkdocs](https://mkdocs.org):

```shell
pip install -r requirements-docs.txt
pip install -e .
mkdocs serve
```

Open http://127.0.0.1:8000/ to view the documentation locally.
