#!/usr/bin/env python3
"""XMLRPC API implementation"""

import xmlrpc.client
from traceback import StackSummary, FrameSummary
from typing import Any, Literal, TypedDict, Union, TypeVar
from types import MethodType
from functools import lru_cache
from .meta import __title__
from .types import Secret, Credentials, Domain, Logic, Env, URL, AskProperty
from .output import Levels, Log, Trace

###########################################################################

ProtocolError = xmlrpc.client.ProtocolError
Fault = xmlrpc.client.Fault
T = TypeVar('T')

###########################################################################


class _Common(type):
    @AskProperty("Enter the Instance URL", Env.INSTANCE)
    def URL(cls) -> URL:
        return getattr(cls, "__url")

    @AskProperty("Enter the Database Name", Env.DATABASE)
    def Database(cls) -> str:
        return getattr(cls, "__database")

    @AskProperty("Enter your Username", Env.USERNAME)
    def Username(cls) -> str:  # pragma: no cover
        return getattr(cls, "__username")

    @AskProperty("Enter your Password (or API-Key)", Env.PASSWORD, secret=True)
    def Password(cls) -> Secret:
        return getattr(cls, "__password")

    @property
    def UID(cls) -> int | Literal[False]:
        return getattr(cls, "__uid")

    @property
    def Loaded(cls) -> bool:
        try:
            return getattr(cls, "__rpc") is not None
        except AttributeError:
            return False

    @property
    def Authorized(cls) -> bool:
        try:
            return bool(cls.UID)
        except AttributeError:
            return False

    @property
    def Arguments(cls) -> tuple[str, str, str]:
        return cls.Database, cls.UID, cls.Password.data

    def __repr__(cls) -> str:
        name = cls.__name__
        attr = ", ".join(
            [f"{p}={repr(getattr(cls, p))}" for p in ["URL", "Database", "Username"]]
        )
        return f"{name}[{attr}]"


class Common(metaclass=_Common):
    """A singleton class representing the Odoo server's common XMLRPC connection."""

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

    def __init__(
        self,
        url: str | None = None,
        database: str | None = None,
        username: str | None = None,
        password: Secret = Secret(''),
        /
    ) -> None:
        """Args:
                url (str, optional): The URL of the  Odoo server.
                database (str, optional): The name of Odoo instance database.
                username (str, optional): The user to authenitcate.
                password (Secret, optional): The user's password.
        """
        if not isinstance(password, Secret):
            raise TypeError("`password` argument must be a Secret type.")

        cls = self.__class__
        setattr(cls, "__url", url)
        setattr(cls, "__database", database)
        setattr(cls, "__username", username)
        setattr(cls, "__password", password)
        getattr(cls, "__uid", False)

    @classmethod
    def Load(cls) -> None:
        """Load the  Odoo server's common XMLRPC connection.
        """
        url = cls.URL

        try:
            assert not cls.Loaded, FileExistsError()

            with Trace():
                setattr(
                    cls,
                    "__rpc",
                    xmlrpc.client.ServerProxy(
                        f"{url}/xmlrpc/2/common",
                        verbose=(Log.Level == Levels.TRACE),
                    ),
                )
        except FileExistsError:
            pass

    @classmethod
    def Authenticate(
        cls,
        *,
        username: str | None = None,
        password: Secret | None = None,
        exit_on_fail: bool = True
    ) -> int:
        """Log in to an Odoo instance's XMLRPC API.

            Args:
                username (str, optional): The user to authenitcate.
                password (Secret, optional): The user's password.
                exit_on_fail (bool, optional): If `True`, calls for an exit on failure. Defaults to True.

            Raises:
                LookupError: Raised when authenitcation fails in any way.

            Returns:
                int: The ID of the authenitcated user.
        """
        def set_and_get(name: str, value: T) -> T:
            if value is not None:
                setattr(cls, f'__{name.lower()}', value)
            return getattr(cls, name)

        try:
            assert not cls.Authorized
            cls.Load()

            rpc = getattr(cls, "__rpc")
            database = cls.Database
            username = set_and_get('Username', username)
            password = set_and_get('Password', password)

            with Trace():
                uid: int | Literal[False] = rpc.authenticate(
                    database, username, password.data, {}
                )

            if not uid:
                err_msg = (
                    f'Could not authenticate the user, "{username}," on the database, "{database}." '
                    'Please check your user and/or password.'
                )
                if exit_on_fail:
                    Log.FATAL(err_msg, code=10)
                else:
                    raise LookupError(err_msg)

            setattr(cls, "__uid", uid)
            return uid
        except AssertionError:
            return cls.UID

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

        def location(headers: dict[str, str]) -> str:
            try:
                return headers["location"]
            except KeyError:
                return headers["Location"]

        result = Credentials()
        url = "https://demo.odoo.com"
        headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Ch-Ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
            ),
        }

        resp = requests.options(url, headers=headers, allow_redirects=False, timeout=3)
        while resp.status_code in [300, 301, 302]:
            url = location(resp.headers)
            resp = requests.options(url, headers=headers, allow_redirects=False)

        if resp.status_code == 303:
            parts: ParseResult = urlparse(url)
            query = {k: "".join(v) for k, v in parse_qs(parts.query).items()}
            result = {
                "instance": f"{parts.scheme}://{parts.netloc}",
                "database": query["dbname"],
                "username": query["user"],
                "password": query["key"],
            }

        return result

    @staticmethod
    def ToStacks(message: str) -> list[tuple[StackSummary, str]]:
        import re

        exc_pattern = r'Traceback +.+:\n((?: .+\n)+)(\S.+)'
        frm_pattern = r'^ *File +"([^"]+)", +line +(\d+), +in +(\w+)\n +(\S.+)'

        stacks: list[tuple[StackSummary, str]] = []
        exceptions = re.findall(exc_pattern, message)

        for exception in exceptions:
            matches = re.findall(frm_pattern, exception[0], flags=re.I | re.M)
            frames = StackSummary([
                FrameSummary(m[0], m[1], m[2], line=m[3], lookup_line=False)
                for m in matches
            ])
            stacks.append((frames, exception[1]))

        return stacks

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

        def print_stack(stack: StackSummary, error: str, first: bool = True) -> None:
            tick = "  -"

            Log.TRACE(stack[0])
            [Log.__send__(tick, frame) for frame in stack[1:]]

            if not first:
                Log.INFO('During handling of the above exception, another exception occurred:')

            Log.ERROR(f"FAULT_ERROR({code}): {error}")

        code = exception.faultCode
        message = exception.faultString
        stacks = Common.ToStacks(message)

        print_stack(*stacks[0])
        [print_stack(*stack, first=False) for stack in stacks[1:]]

        return 100


class _Model(type):

    @lru_cache(maxsize=None)
    def __load__(cls) -> None:
        try:
            assert cls.__rpc
        except AssertionError:
            try:
                Common.Authenticate(exit_on_fail=False)
            except LookupError:
                Common.Authenticate(
                    username='admin',
                    password=Secret('admin')
                )

            with Trace():
                cls.__rpc = xmlrpc.client.ServerProxy(
                    f"{Common.URL}/xmlrpc/2/object",
                    verbose=(Log.Level == Levels.TRACE),
                )


class Model(metaclass=_Model):
    """Performs operations on the records of a specified Odoo model.
    """

    __rpc: xmlrpc.client.ServerProxy = None
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

    @lru_cache(maxsize=None)
    def __new__(cls, name: str, /):
        return super().__new__(cls)

    def __init__(self, name: str, /) -> None:
        """Args:
            name (str): The name of the model to query.
        """
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

            def __execute__(self: Model, *args, **kwargs):
                code = 0

                try:
                    self.__class__.__load__()

                    with Trace():
                        args = args if args else method[1]
                        kwargs = kwargs if kwargs else method[2]

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


###########################################################################

__all__ = [
    "Common",
    "Model",
]

###########################################################################

if __name__ == "__main__":
    print(f"{__title__} - {__doc__}")  # pragma: no cover
