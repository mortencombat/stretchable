"""
Contains helper methods used for parsing of CSS-based styles.
"""

from typing import Callable, Iterable

import tinycss2


def strip(
    nodes: list[tinycss2.ast.Node],
    *,
    predicate: Callable[[tinycss2.ast.Node], bool] = lambda node: node
    and isinstance(node, tinycss2.ast.WhitespaceToken),
    leading: bool = True,
    internal: bool = False,
    trailing: bool = True,
) -> list[tinycss2.ast.Node]:
    """
    Strip leading, internal and/or trailing tokens matching a given predicate
    (default: WhitespaceTokens) from the given list of nodes.
    """

    s = [predicate(node) for node in nodes]
    j, k = None, None
    for i, v in enumerate(s):
        if v:
            continue
        if j is None:
            j = i
        k = i

    return [
        node
        for i, node in enumerate(nodes)
        if (
            (not leading or j is None or i >= j)
            and (not trailing or k is None or i <= k)
            and (not internal or not s[i])
        )
    ]


def split(
    nodes: list[tinycss2.ast.Node],
    sep: str = None,
    *,
    predicate: Callable[[tinycss2.ast.Node], bool] = None,
    maxsplit: int = -1,
) -> list[list[tinycss2.ast.Node]]:
    """
    Splits a list of tokens by a specified separator (string literal or
    determined by a predicate method).
    """

    if maxsplit == 0:
        raise ValueError("`maxsplit` cannot be 0")

    if sep is not None:
        if predicate is not None:
            raise ValueError("Provide either `sep` or `predicate`, not both")
        predicate = (
            lambda node: node
            and isinstance(node, tinycss2.ast.LiteralToken)
            and node.value == sep
        )

    if predicate is None:
        raise ValueError("Separator is required, either via `sep` or `predicate`")

    sets, cur = [], []
    for node in nodes:
        if (maxsplit < 0 or len(sets) < maxsplit) and predicate(node):
            sets.append(cur)
            cur = []
        else:
            cur.append(node)
    sets.append(cur)

    return sets


def parse_rules(value: str) -> list[tinycss2.ast.Declaration]:
    """Parse the content of a style property into a list of declarations."""
    return tinycss2.parse_blocks_contents(
        value, skip_comments=True, skip_whitespace=True
    )


def map_rules(
    rules: list[tinycss2.ast.Declaration],
    props: Iterable[str] = None,
) -> dict[str, tinycss2.ast.Declaration]:
    """
    Map a list of declarations into a dictionary, optionally filtering by
    declaration/property name.
    """

    mapped = dict()
    for rule in rules:
        if props and rule.name not in props:
            continue
        mapped[rule.name] = rule

    return mapped


def get_prop_values(
    source: dict[str, tinycss2.ast.Declaration],
    props: Iterable[str],
    shorthands: dict[
        str, Callable[[list[tinycss2.ast.Node]], dict[str, list[tinycss2.ast.Node]]]
    ] = None,
    *,
    default: None | list[tinycss2.ast.Node] | Callable[[str], tinycss2.ast.Node] = None,
    as_dict: bool = False,
    remove_consumed_from_source: bool = False,
) -> tuple[list[tinycss2.ast.Node]] | dict[str, list[tinycss2.ast.Node]]:
    """
        Gets 'effective' property values from a list of declarations, with support
        for recursive parsing of shorthand properties.

        First looks for any of `props` in source, and sets the initial values of
        those in the result dict.

        Then looks for any of the shorthands in source. If any are found, uses the
        provided method to split those into corresponding components. If any of the
        resulting components are not in `props`, check if they themselves are
        shorthands and recursively process them. An exception will be raised (or a
    ()    warning?) if any of the output components cannot be processed into targets.

        The default value assigned to targets (if they are not defined in `source`)
        can be either None, a list of nodes or a callable which takes the target
        identifier and returns the default value.

        Returns:

            If as_dict, returns a dict. If default is None and a property value is
            not available, the property is not included in the dict.

            If not as_dict (default), returns a tuple of property values in same
            order as `props`. All properties are included, even if a value is not
            available and the default is None.

    """

    # Look for explicit declarations of `props`, apply default value if explicit value is not available.
    values = dict()
    for prop in props:
        if prop not in source:
            continue
        values[prop] = source[prop].value
        if remove_consumed_from_source:
            del source[prop]

    # Process shorthands recursively.
    def process_shorthand(prop: str, value: list[tinycss2.ast.Node]) -> None:
        if prop not in shorthands:
            # Property is present, but we cannot process it
            raise ValueError(f"Unrecognized property '{prop}'")

        for _name, _value in shorthands[prop](value).items():
            # If a property name is identical to one of `props`, and the value is not yet set, set it.
            if _name in props:
                if _name not in values:
                    values[_name] = _value
                continue

            # If a property name is not one of `props`, attempt to process as a shorthand.
            process_shorthand(_name, _value)

        if remove_consumed_from_source and prop in source:
            del source[prop]

    for prop in shorthands:
        if prop not in source:
            continue
        process_shorthand(prop, source[prop].value)

    # Set default values for missing properties, if applicable
    if default is not None:
        for prop in props:
            if prop in values:
                continue
            values[prop] = default() if callable(default) else default

    # Return prop values
    if as_dict:
        return values
    return tuple(values[prop] if prop in values else None for prop in props)
