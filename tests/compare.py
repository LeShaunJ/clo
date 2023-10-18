import typing as _t

T = _t.TypeVar("T")
OP = _t.Literal["__eq__", "__ne__", "__lt__", "__gt__", "__le__", "__ge__"]


class CMP(_t.NamedTuple):
    operator: OP
    value: _t.Any


def EQ(value: T):
    return CMP("__eq__", value)


def NE(value: T):
    return CMP("__ne__", value)


def LT(value: T):
    return CMP("__lt__", value)


def GT(value: T):
    return CMP("__gt__", value)


def LE(value: T):
    return CMP("__le__", value)


def GE(value: T):
    return CMP("__ge__", value)


__all__ = [
    'CMP', 'EQ', 'NE', 'LT', 'GT', 'LE', 'GE'
]
