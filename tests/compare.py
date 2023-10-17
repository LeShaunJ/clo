import typing as _t

T = _t.TypeVar("T")


class GenericMeta(type):
    pass


class _NamedTupGen(_t.NamedTupleMeta, GenericMeta):
    pass


class CMP(_t.NamedTuple, _t.Generic[T], metaclass=_NamedTupGen):
    operator: _t.Literal["__eq__", "__ne__", "__lt__", "__gt__", "__le__", "__ge__"]
    value: T


def EQ(value: T) -> CMP[T]:
    return CMP("__eq__", value)


def NE(value: T) -> CMP[T]:
    return CMP("__ne__", value)


def LT(value: T) -> CMP[T]:
    return CMP("__lt__", value)


def GT(value: T) -> CMP[T]:
    return CMP("__gt__", value)


def LE(value: T) -> CMP[T]:
    return CMP("__le__", value)


def GE(value: T) -> CMP[T]:
    return CMP("__ge__", value)


__all__ = [
    'CMP', 'EQ', 'NE', 'LT', 'GT', 'LE', 'GE'
]
