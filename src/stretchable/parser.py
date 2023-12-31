from __future__ import annotations

import io
import logging
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Iterable, Optional, Protocol

import cssselect2
import tinycss2
from attrs import define
from lxml import etree

from .node import Node
from .style import Style

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class UnsupportedElementError(Exception):
    ...


class ElementType(Enum):
    # The element contains style rules
    STYLES = auto()
    # The element is the root node
    ROOT = auto()
    # The element is a child node
    CHILD = auto()
    # The element can be skipped silently
    SKIP = auto()
    # The element is unsupported
    UNSUPPORTED = auto()


@define
class DeclarationStore:
    """
    The DeclarationStore manages storing of CSS declarations (along with
    specificity) and listing and retrieval of applicable CSS attributes.

    Consider read-only dictionary-type access (mapping?)

    """

    def add(
        self,
        declaration: tinycss2.parser.Declaration
        | Iterable[tinycss2.parser.Declaration],
        *,
        inline: bool = False,
        specificity: Optional[tuple[int, int, int]] = None,
    ) -> None:
        """

        For specificity, prepend inline:
        inline - ID - CLASS - TYPE
        Calculate a corresponding single integer (using bitwise arithmetic?)
        where the highest value takes precedence if the same CSS attribute is
        specified in more than one declaration.

        """

        ...


class NodeFactory(Protocol):
    def get_type(self, element: etree.Element) -> ElementType:
        """Return the type of the element.

        If the type returned is STYLE or SKIP, any child elements will be
        ignored.
        """

    def process_element_tree(
        self, root: etree.Element, fileprovider: FileProvider
    ) -> tuple[
        etree.Element, Iterable[tinycss2.parser.AtRule | tinycss2.parser.QualifiedRule]
    ]:
        """Processes the element tree, returns the root element and any style rules."""
        ...

    # def process_element(
    #     self, element: etree.Element, fileprovider: FileProvider
    # ) -> None:
    #     """Processes the element, optionally modifying or removing it from the tree."""

    def get_styles(
        self,
        element: etree.Element,
        fileprovider: FileProvider,
    ) -> Iterable[tinycss2.parser.AtRule | tinycss2.parser.QualifiedRule]:
        """Return the style rules from the element.

        If the element links to another file, `fileprovider` should be used to
        get the file.
        """

    def get_node(
        self,
        tag: str,
        style: Style,
        children: list[Node],
        content: str,
        attributes: dict[str, str | int | None],
    ) -> Node:
        """Return a Node instance if possible, otherwise raise UnsupportedElementError."""
        ...


class FileType(Enum):
    XML = "xml"
    XHTML = "xhtml"
    HTML = "html"
    CSS = "css"


class FileProvider(Protocol):
    # TODO: fileprovider should be able to pass either just the filepath, or the contents.
    def read(filepath: Path) -> tuple[str | Path, FileType]:
        ...


class HTMLNodeFactory:
    """A basic implementation of NodeFactory that supports styles from
    <style> elements and <link ... />, and nodes from <body> and <div> elements
    with no content."""

    def process_element_tree(
        self, root: etree.Element, fileprovider: FileProvider
    ) -> tuple[
        etree.Element, Iterable[tinycss2.parser.AtRule | tinycss2.parser.QualifiedRule]
    ]:
        """Processes the element tree, returns the root element (<body>) and any style rules."""

        # Iterate over the tree and:
        # - record the root element (<body>)
        # - Obtain style rules from any style elements
        # - Within the root element tree, discard any elements which are not type ElementType.CHILD

        def process_element(
            element: etree.Element, *, in_root_tree: bool = False
        ) -> bool:
            """Return True if element should be removed from tree"""
            t = self.get_type(element)

            if t == ElementType.STYLES:
                nonlocal rules
                rules.extend(self.get_styles(element, fileprovider))

            if t == ElementType.ROOT:
                nonlocal root_element
                if root_element is not None:
                    raise Exception("Multiple root elements not supported")
                root_element = element

            for child in element:
                rm = process_element(
                    child, in_root_tree=in_root_tree or t == ElementType.ROOT
                )
                if rm:
                    element.remove(child)

            return in_root_tree and t not in (ElementType.ROOT, ElementType.CHILD)

        root_element = None
        rules: list[tinycss2.parser.AtRule | tinycss2.parser.QualifiedRule] = []
        process_element(root)
        return root_element, rules

    def get_type(self, element: etree.Element) -> ElementType:
        # Supported style elements
        if element.tag == "style":
            return ElementType.STYLES
        if element.tag == "link" and "rel" in element.attrib:
            return ElementType.STYLES

        # Supported node elements
        parent = element.getparent()
        if element.tag == "body":
            if parent.tag != "html":
                return ElementType.UNSUPPORTED
            return ElementType.ROOT
        if element.tag == "div":
            if parent.tag not in ("body", "div"):
                return ElementType.UNSUPPORTED
            return ElementType.CHILD

        return ElementType.SKIP

    def get_styles(
        self,
        element: etree.Element,
        fileprovider: FileProvider,
    ) -> Iterable[tinycss2.parser.AtRule | tinycss2.parser.QualifiedRule]:
        """Return the style rules from the element."""

        if element.tag == "style":
            return tinycss2.parse_stylesheet(
                element.text, skip_comments=True, skip_whitespace=True
            )

        if element.tag == "link":
            # Verify attributes and read/parse stylesheet from linked file
            ...
            return []

        raise Exception("Element does not contain styles")

    def get_node(
        self,
        tag: str,
        style: Style,
        children: list[Node],
        content: str,
        attributes: dict[str, str | int | None],
    ) -> Node:
        if tag not in ("body", "div"):
            raise UnsupportedElementError(
                "Only <body> and <div> elements are supported"
            )

        if content is not None:
            content = content.strip()
        if content:
            raise UnsupportedElementError("Elements containing text are not supported")
        for attr, value in attributes.items():
            logger.warn(
                "Attribute '%s' ('%s') is unsupported and will be ignored", attr, value
            )
        return Node(*children, style=style)


class StandardFileProvider:
    """Standard implementation of FileProvider with no preprocessing of files."""

    def read(filepath: Path) -> tuple[str | Path, FileType]:
        if not isinstance(filepath, Path):
            filepath = Path(filepath)


# def load(
#     filepath: Path,
#     *,
#     elementfactory: Optional[NodeFactory] = None,
#     fileprovider: Optional[FileProvider] = None,
# ) -> Node:
#     """Parse XML/HTML from file into a node tree."""

#     if not fileprovider:
#         fileprovider = StandardFileProvider()
#     with fileprovider.open(filepath) as f:
#         return loads(
#             f,
#             elementfactory=elementfactory,
#             fileprovider=fileprovider,
#         )


def loads(
    content: io.BytesIO | io.StringIO | str | bytes,
    *,
    nodefactory: Optional[NodeFactory] = None,
    fileprovider: Optional[FileProvider] = None,
) -> Node:
    """Parse a string, bytes array or stream of an HTML/XML document into a node tree."""

    # def iterup(element: etree.Element, method: Callable[[etree.Element], None]):
    #     """Walks the tree and applies `method` to all elements starting with the
    #     deepest elements and walking up the tree."""
    #     for e in element:
    #         iterup(e, method)
    #     method(element)

    # TODO: Determine if content is XML/XHTML or HTML.
    is_HTML = True

    if not nodefactory:
        if not is_HTML:
            raise ValueError("`nodefactory` is required for parsing XML")
        nodefactory = HTMLNodeFactory()

    """
    Process:

    - Parse XML/HTML to element tree
    - Preprocess elements:
        - Locate root element (there must be one and only one root element) and make a note of it
        - Assemble style rules
        - Modify/remove elements within root element tree that are not applicable/relevant
    - Create ElementWrapper from root element
    - Create nodes from root element and child elements

    """

    # Parse tree
    parser = etree.HTMLParser() if is_HTML else None
    tree = etree.parse(content, parser)

    # Process element tree using NodeFactory, get root element and style rules
    root, rules = nodefactory.process_element_tree(tree.getroot(), fileprovider)
    if root is None:
        raise Exception("Root element is required")

    # Build CSS matcher
    matcher = cssselect2.Matcher()
    for rule in rules:
        selectors = cssselect2.compile_selector_list(rule.prelude)
        declarations = tinycss2.parse_declaration_list(
            rule.content, skip_comments=True, skip_whitespace=True
        )
        for selector in selectors:
            matcher.add_selector(selector, declarations)

    # Create element wrapper for selector matching
    tree = (
        cssselect2.ElementWrapper.from_html_root
        if is_HTML
        else cssselect2.ElementWrapper.from_xml_root
    )(root)

    # Create nodes
    def get_node(
        element: cssselect2.ElementWrapper, *, is_root: bool = False
    ) -> Node | None:
        # Check element type
        t = nodefactory.get_type(element.etree_element)
        if t == ElementType.UNSUPPORTED or t == ElementType.STYLES:
            raise UnsupportedElementError
        if t == ElementType.SKIP and is_root:
            raise Exception("Cannot skip the root node")
        if t == ElementType.ROOT and not is_root:
            raise Exception("There can only be a single root node")
        if t == ElementType.CHILD and is_root:
            raise Exception("Element is not a root node")

        children = []
        for child in element.iter_children():
            node = get_node(child)
            if node is None:
                continue
            children.append(node)

        # Create style
        matches = matcher.match(element)
        declarations = DeclarationStore()
        for match in matches:
            # meaning of 'order' and 'pseudo' is unclear, they are presently discarded
            specificity, order, pseudo, decls = match
            declarations.add(decls, specificity=specificity)

        # get additional (overriding) styles from style attrib (if present)
        style = element.etree_element.get("style", None)
        if style:
            declarations.add(
                tinycss2.parse_declaration_list(
                    style, skip_comments=True, skip_whitespace=True
                ),
                inline=True,
            )
            del element.etree_element.attrib["style"]

        # for s in styles:
        #     print(s)

        # TODO: Style.from_declarations(declarations)
        style = None

        # Create node
        return nodefactory.get_node(
            element.etree_element.tag,
            style,
            children,
            element.etree_element.text,
            element.etree_element.attrib,
        )

    return get_node(tree, is_root=True)
