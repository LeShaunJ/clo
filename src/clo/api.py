#!/usr/bin/env python3
"""XMLRPC API implementation"""

import xmlrpc.client
import ssl
from typing import Any, Literal, TypedDict, Union
from types import MethodType
from functools import lru_cache
from itertools import groupby
from .meta import __title__
from .types import Secret, IR, Credentials, Domain, Logic
from .output import Levels, Log, Trace

###########################################################################

ProtocolError = xmlrpc.client.ProtocolError
Fault = xmlrpc.client.Fault

###########################################################################


def IRWalk(*models: IR, depth: int = 0) -> dict[str, IR]:  # pragma: no cover

    def transform(obj: IR):
        try:
            path = obj["model"].split(".")[depth:]
            return IR({**obj, "model": path[-1], "path": path})
        except IndexError:
            return obj

    def structure(key: str, *objs: IR) -> IR:
        children = IRWalk(*objs, depth=(depth + 1))
        parent = ([c for n, c in children.items() if n == key] or [IR({"model": key})])[
            0
        ]
        ...
        children = {n: c for n, c in children.items() if c != parent}
        ...
        return IR({**parent, "children": children})

    models = [transform(m) for m in models]

    try:
        groups = groupby(models, lambda m: m["path"][depth])
        return {k: structure(k, *g) for k, g in groups}
    except IndexError:
        return {m["model"]: m for m in models}


###########################################################################


class _Common(type):

    @property
    def URL(cls) -> str:
        return getattr(cls, "__url")

    @property
    def Database(cls) -> str:
        return getattr(cls, "__database")

    @property
    def Username(cls) -> str:  # pragma: no cover
        return getattr(cls, "__username", "")

    @property
    def UID(cls) -> int | Literal[False]:
        return getattr(cls, "__uid", False)

    @property
    def Arguments(cls) -> tuple[str, str, str]:
        return cls.Database, cls.UID, getattr(cls, "__password").data


class Common(metaclass=_Common):
    """A singleton class representing the Odoo server's common XMLRPC connection.
    """

    class APIVersion(TypedDict):
        """A collection of version metadata properties:

        - **server_version** `str`: The major and minor version.
        - **server_version_info** `(int, int, int, str, int)`: The major, minor, patch, release, and build items.
        - **server_serie** `str`
        - **protocol_version** `int`: The API protocol version.
        """

        server_version: str
        server_version_info: tuple[int, int, int, str, int]
        server_serie: str
        protocol_version: int

    @classmethod
    def Load(cls, url: str) -> None:
        """Load the  Odoo server's common XMLRPC connection.

        Args:
            url (str): The URL of the  Odoo server.
        """

        setattr(cls, "__url", url)
        ...
        try:
            with Trace():
                setattr(
                    cls,
                    "__rpc",
                    xmlrpc.client.ServerProxy(
                        f"{url}/xmlrpc/2/common",
                        verbose=(Log.Level == Levels.TRACE),
                    ),
                )
        except OSError:
            Log.FATAL(f"Could not connect to XML-RPC protocol at {url}")

    @classmethod
    def Authenticate(
        cls,
        database: str,
        username: str,
        password: Secret,
        *,
        exit_on_fail: bool = True,
    ) -> int:
        """Log in to an Odoo instance's XMLRPC API.

        Args:
            database (str): The name of Odoo instance database.
            username (str): The user to authenitcate.
            password (Secret): The user's password.
            exit_on_fail (bool, optional): If `True`, calls for an exit on failure. Defaults to True.

        Raises:
            LookupError: Raised when authenitcation fails in any way.

        Returns:
            int: The ID of the authenitcated user.
        """

        setattr(cls, "__database", database)
        setattr(cls, "__username", username)
        setattr(cls, "__password", password)
        ...
        rpc = getattr(cls, "__rpc")
        with Trace():
            uid: int | Literal[False] = rpc.authenticate(
                database, username, password.data, {}
            )
        if not uid:
            err_msg = f'Could not authenticate the user, "{username}," on the database, "{database}." \
                Please check your user and/or password.'
            if exit_on_fail:
                Log.FATAL(err_msg, code=10)
            else:
                raise LookupError(err_msg)
        ...
        setattr(cls, "__uid", uid)
        return uid

    @classmethod
    def Version(cls) -> APIVersion:
        """Retrieve version data about the Odoo instance.

        Returns:
            APIVersion: The version properties.
        """

        with Trace():
            return getattr(cls, "__rpc").version()

    @classmethod
    def Demo(cls) -> Credentials:
        """Retrieve demo credentials from Odoo Cloud.

        Returns:
            Credentials: Teh credentials, in the for of Environment Variable declarations.
        """

        from urllib.parse import urlparse, parse_qs, ParseResult
        import requests

        ...

        def location(headers: dict[str, str]) -> str:
            try:
                return headers["location"]
            except KeyError:
                return headers["Location"]

        ...
        result = Credentials()
        url = "https://demo.odoo.com"
        ...
        resp = requests.post(url, allow_redirects=False)
        while resp.status_code in [300, 301, 302]:
            url = location(resp.headers)
            resp = requests.post(url, allow_redirects=False)
        ...
        if resp.status_code == 303:
            resp = requests.get(url, allow_redirects=False)
            ...
            parts: ParseResult = urlparse(location(resp.headers))
            query = {k: "".join(v) for k, v in parse_qs(parts.query).items()}
            result = {
                "instance": f"{parts.scheme}://{parts.netloc}",
                "database": query["dbname"],
                "username": query["user"],
                "password": query["key"],
            }
        ...
        return result

    @staticmethod
    def HandleProtocol(exception: xmlrpc.client.ProtocolError) -> Literal[200]:
        """A handler for protocal errors.

        Args:
            exception (xmlrpc.client.ProtocolError): The protocol exception.

        Returns:
            Literal[200]: Standard exit code for protocol errors in `clo`.
        """

        Log.ERROR(f"PROTOCOL_ERROR({exception.errcode}): {exception.errmsg}")
        if Log.Level == Levels.DEBUG:
            Log.DEBUG(f"URL: {exception.url}\n  ")
            Log.DEBUG("HEADERS:")
            for key, val in exception.headers:
                Log.DEBUG(f"- {key}: {val}")
        return 200

    @staticmethod
    def HandleFault(exception: xmlrpc.client.Fault) -> Literal[100]:
        """A handler for fault errors.

        Args:
            exception (xmlrpc.client.ProtocolError): The fault exception.

        Returns:
            Literal[100]: Standard exit code for protocol errors in `clo`.
        """

        Log.ERROR(f"FAULT_ERROR({exception.faultCode}): {exception.faultString}")
        return 100


class _Model(type):
    __rpc = None
    ...
    IR: "Model" = None
    Repo: dict[str, IR] = {}
    ...

    @lru_cache(maxsize=None)
    def __getitem__(cls, __name: str, /):
        try:
            if not cls.IR:
                cls.__refresh__()
            ...
            assert __name in cls.Repo
            ...
            return cls(f"{__name}")
        except AssertionError:
            Log.FATAL(f'The model "{__name}" is invalid.', code=20)

    ...

    def __refresh__(cls) -> None:
        cls.IR = cls("ir.model")
        ...
        models = sorted(cls.IR.Find(fields=["model", "info"]), key=lambda m: m["model"])
        cls.Repo = {m["model"]: IR(m) for m in models}


class Model(metaclass=_Model):
    """Perform operation on the records of a specified Odoo model.

    ```python
    Model[str]
    ```

    Args:
        name (str): The name of the model to query.
    """

    __rpc = None
    __name = ""
    __methods__: dict[str, tuple[str, list, dict]] = {
        "Search": ("search", [[]], {}),
        "Count": ("search_count", [[]], {}),
        "Find": ("search_read", [[]], {}),
        "Read": ("read", [], {}),
        "Write": ("write", [], {}),
        "Create": ("create", [], {}),
        "Delete": ("unlink", [], {}),
        "Fields": ("fields_get", [[]], {}),
    }

    IR: "Model" = None
    Repo: dict[str, IR] = {}

    def __new__(cls, *args):
        if not cls.__rpc:
            with Trace():
                cls.__rpc = xmlrpc.client.ServerProxy(
                    f"{Common.URL}/xmlrpc/2/object",
                    verbose=(Log.Level == Levels.TRACE),
                )
        ...
        return super().__new__(cls)

    def __init__(self, name: str, /) -> None:
        self.__name = name

    def __str__(self) -> str:
        return self.__name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}['{self}']"

    @lru_cache(maxsize=None)
    def __getattribute__(self, __name: str) -> Any:
        get_attr = object.__getattribute__
        try:
            method: tuple[str, list, dict] = get_attr(self, "__methods__")[__name]
            ...

            def __execute__(self: Model, *args, **kwargs):
                code = 0
                try:
                    import sys
                    with Trace():
                        args = args if args else method[1]
                        kwargs = kwargs if kwargs else method[2]
                        # Log.DEBUG(*(*Common.Arguments, self.__name, method[0], args, kwargs), sep=', ')
                        return self.__rpc.execute_kw(
                            *Common.Arguments, self.__name, method[0], args, kwargs
                        )
                except xmlrpc.client.ProtocolError as p:
                    Common.HandleProtocol(p)
                except xmlrpc.client.Fault as f:
                    Common.HandleFault(f)
                except Exception as e:
                    code = 30
                    Log.ERROR(e)
                finally:
                    if code > 0:
                        raise Log.EXIT(code=code)

            ...
            return MethodType(__execute__, self)
        except KeyError:
            return get_attr(self, __name)

    def Search(
        self,
        domain: list[Union[Domain, Logic]] = [],
        /,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[int]:
        """Searches for record IDs based on the search domain.

        Args:
            domain (list[Union[Domain, Logic]], optional): A set of criterion to filter the search
                by.
            offset (int, optional): Number of results to ignore.
            limit (int | None, optional): Maximum number of records to return.
            order (str | None, optional): The field to sort the records by.

        Returns:
            list[int]: A list of matched record IDs.
        """
        ...

    def Count(
        self, domain: list[Union[Domain, Logic]] = [], /, limit: int | None = None
    ) -> int:
        """Returns the number of records in the current model matching
        the provided domain.

        Args:
            domain (list[Union[Domain, Logic]], optional): A set of criterion to filter the search
                by.
            limit (int | None, optional): Maximum number of records to return.

        Returns:
            int: The count of matched records.
        """
        ...

    def Find(
        self,
        domain: list[Union[Domain, Logic]] = [],
        /,
        fields: list[str] = [],
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        """A shortcut that combines `search` and `read` into one execution.

        Args:
            domain (list[Union[Domain, Logic]], optional): A set of criterion to filter the search
                by.
            fields (list[str], optional): Field names to return (default is all fields).
            offset (int, optional): Number of results to ignore.
            limit (int | None, optional): Maximum number of records to return.
            order (str | None, optional): The field to sort the records by.

        Returns:
            list[dict[str, Any]]: A list of matched record data.
        """
        ...

    def Read(self, ids: list[int], /, fields: list[str] = []) -> list[dict[str, Any]]:
        """Retrieves the details for the records at the ID(s) specified.

        Args:
            ids (list[int]): The ID number(s) of the record(s) to perform the action on. Specifying
                `-` expects a space-separated list from STDIN.
            fields (list[str], optional): Field names to return (default is all fields).

        Returns:
            list[dict[str, Any]]: A list of record data.
        """
        ...

    def Write(self, ids: list[int], values: dict[str, Any], /) -> bool:
        """Updates existing records in the current model.

        Args:
            ids (list[int]): The ID number(s) of the record(s) to perform the action on. Specifying
                `-` expects a space-separated list from STDIN.
            values (dict[str, Any]): Key/value pair(s) that correspond to the field and assigment to
                be made, respectively.

        Returns:
            bool: `True`, if the operation was successful.
        """
        ...

    def Create(self, values: dict[str, Any], /) -> int:
        """Creates new records in the current model.

        Args:
            values (dict[str, Any]): Key/value pair(s) that correspond to the field and assigment to
                be made, respectively.

        Returns:
            int: The ID of the created record.
        """
        ...

    def Delete(self, ids: list[int], /) -> bool:
        """Deletes the records from the current model.

        Args:
            ids (list[int]): The ID number(s) of the record(s) to perform the action on. Specifying
                `-` expects a space-separated list from STDIN.

        Returns:
            bool: `True`, if the operation was successful.
        """
        ...

    def Fields(self, *, attributes: list[str] = []) -> dict[str, dict[str, Any]]:
        """Retrieves raw details of the fields available in the current model.
        For user-friendly formatting, run `%(prog)s explain fields`

        Args:
            attributes (list[str], optional): Attribute(s) to return for each field, all if
                empty or not provided.

        Returns:
            dict[str, dict[str, Any]]: A collection of fields and their metadata.
        """
        ...

    ...


###########################################################################

__all__ = [
    'Common',
    'Model',
]

###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")  # pragma: no cover
