"""Narrowing of untyped input (JSON, argv) to declared types, as pure functions: the scripts parse once at the edge
and work with typed values from there."""
import json
from collections.abc import Mapping, Sequence
from typing import cast


def parse_json(text: str | bytes) -> object:
    data: object = json.loads(text)
    return data


def load_json(path: str) -> object:
    with open(path, encoding="utf-8") as f:
        return parse_json(f.read())


# The as_* helpers stop with a message naming `where` (file and key path) so a bad config file is reported by what it is,
# # not by a traceback; they return fresh typed copies, so callers never touch the untyped original.
def as_dict(value: object, where: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise SystemExit(f"{where}: expected an object")
    return {str(k): v for k, v in cast("dict[object, object]", value).items()}


def as_list(value: object, where: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise SystemExit(f"{where}: expected a list")
    return tuple(cast("list[object]", value))


def as_str(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise SystemExit(f"{where}: expected a string")
    return value


# bool is a subclass of int in Python; true/false in a JSON file is not an integer here.
def as_int(value: object, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SystemExit(f"{where}: expected an integer")
    return value


def member(obj: Mapping[str, object], key: str, where: str) -> object:
    if key not in obj:
        raise SystemExit(f"{where}: missing '{key}'")
    return obj[key]


def str_map(value: object, where: str) -> Mapping[str, str]:
    return {k: as_str(v, f"{where}.{k}") for k, v in as_dict(value, where).items()}


def take_option(args: Sequence[str], name: str) -> tuple[str | None, tuple[str, ...]]:
    """The value after the option `name`, and the arguments without the option and its value."""
    if name not in args:
        return None, tuple(args)
    i = args.index(name)
    if i + 1 >= len(args):
        raise SystemExit(f"{name} needs a value")
    return args[i + 1], (*args[:i], *args[i + 2:])


def take_flag(args: Sequence[str], name: str) -> tuple[bool, tuple[str, ...]]:
    return name in args, tuple(a for a in args if a != name)


# 'a,b' -> {'a', 'b'}; None (option not given) means no filter, not an empty one.
def split_ids(value: str | None) -> frozenset[str] | None:
    return None if value is None else frozenset(value.split(","))
