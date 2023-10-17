#!/usr/bin/env python3
"""XMLRPC API implementation"""

import xmlrpc.client
import ssl
from typing import Any, Literal, TypedDict
from types import MethodType
from functools import cache
from itertools import groupby
from .meta import __title__
from .types import Secret, IR, Credentials
from .output import Log, Trace

###########################################################################

ProtocolError = xmlrpc.client.ProtocolError
Fault = xmlrpc.client.Fault

###########################################################################


def IRWalk(*models: IR, depth: int = 0) -> dict[str, IR]:

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


class CookiesTransport(xmlrpc.client.SafeTransport):
    """A Transport subclass that retains cookies over its lifetime."""

    __instance: "CookiesTransport" = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, context=ssl._create_unverified_context()):
        super().__init__(context=context)
        self._cookies = []

    def send_headers(self, connection, headers):
        if self._cookies:
            connection.putheader("Cookie", "; ".join(self._cookies))
        super().send_headers(connection, headers)

    def parse_response(self, response):
        # This check is required if in some responses we receive no cookies at all
        if response.msg.get_all("Set-Cookie"):
            for header in response.msg.get_all("Set-Cookie"):
                cookie = header.split(";", 1)[0]
                self._cookies.append(cookie)
        return super().parse_response(response)


class _Common(type):
    ...
    __instance = None
    ...

    @property
    def URL(cls) -> str:
        return getattr(cls, "__url")

    @property
    def Database(cls) -> str:
        return getattr(cls, "__database")

    @property
    def Username(cls) -> str:
        return getattr(cls, "__username", "")

    @property
    def UID(cls) -> int | Literal[False]:
        return getattr(cls, "__uid", False)

    @property
    def Arguments(cls) -> tuple[str, str, str]:
        return cls.Database, cls.UID, getattr(cls, "__password").data

    ...

    def __new__(cls, name: str, bases: tuple[type], dct: dict):
        if not cls.__instance:
            cls.__instance = type.__new__(cls, name, bases, dct)
        ...
        return cls.__instance


class Common(metaclass=_Common):
    ...

    class APIVersion(TypedDict):
        server_version: str
        server_version_info: tuple[int, int, int, str, int, str]
        server_serie: str
        protocol_version: int

    ...

    @classmethod
    def Load(cls, url: str) -> None:
        setattr(cls, "__url", url)
        ...
        try:
            with Trace():
                setattr(
                    cls,
                    "__rpc",
                    xmlrpc.client.ServerProxy(
                        f"{url}/xmlrpc/2/common",
                        transport=CookiesTransport(),
                        verbose=(Log.Level == Log.Levels.TRACE),
                    ),
                )
        except OSError:
            Log.FATAL(f"Could not connect to XML-RPC protocol at {url}")

    ...

    @classmethod
    def Authenticate(
        cls,
        database: str,
        username: str,
        password: Secret,
        *,
        exit_on_fail: bool = True,
    ) -> int:
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

    ...

    @classmethod
    def Version(cls) -> APIVersion:
        with Trace():
            return getattr(cls, "__rpc").version()

    ...

    @classmethod
    def Demo(cls) -> Credentials:
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

    ...

    @staticmethod
    def HandleProtocol(p: xmlrpc.client.ProtocolError) -> int:
        Log.ERROR(f"PROTOCOL_ERROR({p.errcode}): {p.errmsg}")
        if Log.Level == Log.Levels.DEBUG:
            Log.DEBUG(f"URL: {p.url}\n  ")
            Log.DEBUG("HEADERS:")
            for key, val in p.headers:
                Log.DEBUG(f"- {key}: {val}")
        return 200

    ...

    @staticmethod
    def HandleFault(f: xmlrpc.client.Fault) -> int:
        Log.ERROR(f"FAULT_ERROR({f.faultCode}): {f.faultString}")
        return 100

    ...


class _Model(type):
    __rpc = None
    ...
    IR: "Model" = None
    Repo: dict[str, IR] = {}
    ...

    @cache
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
    ...
    IR: "Model" = None
    Repo: dict[str, IR] = {}
    ...

    def __new__(cls, *args):
        if not cls.__rpc:
            with Trace():
                cls.__rpc = xmlrpc.client.ServerProxy(
                    f"{Common.URL}/xmlrpc/2/object",
                    transport=CookiesTransport(),
                    verbose=(Log.Level == Log.Levels.TRACE),
                )
        ...
        return super().__new__(cls)

    ...

    def __init__(self, name: str, /) -> None:
        self.__name = name

    ...

    def __str__(self) -> str:
        return self.__name

    ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}['{self}']"

    ...

    @cache
    def __getattribute__(self, __name: str) -> Any:
        get_attr = object.__getattribute__
        try:
            method: tuple[str, list, dict] = get_attr(self, "__methods__")[__name]
            ...

            def __execute__(self: Model, *args, **kwargs):
                code = 0
                try:
                    import sys
                    print(args, kwargs, file=sys.__stdout__)
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

    ...

    def Search(
        self,
        domain: list[tuple[str, str, str]] = [],
        /,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
        count: bool = False,
    ) -> list[int]:
        ...

    def Count(
        self, domain: list[tuple[str, str, str]] = [], /, limit: int | None = None
    ) -> list[int]:
        ...

    def Find(
        self,
        domain: list[tuple[str, str, str]] = [],
        /,
        fields: list[str] = [],
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
        count: bool = False,
    ) -> list[dict[str, Any]]:
        ...

    def Read(self, ids: list[int], /, fields: list[str] = []) -> list[dict[str, Any]]:
        ...

    def Write(self, ids: list[int], values: dict[str, Any], /) -> bool | None:
        ...

    def Create(self, values: dict[str, Any], /) -> int:
        ...

    def Delete(self, ids: list[int], /) -> bool | None:
        ...

    def Fields(self, *, attributes: list[str] = []) -> dict[str, dict[str, Any]]:
        ...

    ...


###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")
