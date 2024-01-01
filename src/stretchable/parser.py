from __future__ import annotations

import io
import logging
from collections.abc import Mapping
from enum import Enum, auto
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Protocol

import cssselect2
import tinycss2
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


class Styles(Mapping):
    """
    Manages storing of CSS style declarations (considering specificity) and
    listing and retrieval of corresponding, effective CSS properties.

    WORKING NOTES:

    Consider the following approach:
    - Shorthand properties are resolved to all of the individual properties which are then set
    - A property is overrided only if the specificity score of another value is higher

    Requirements:
    - Must be able to track which properties have been set

    Possible drawbacks:
    - When creating the style, it is necessary to have both properties which have been set as well as properties that have their default values.
      And the default values should probably be able to be user-specified?

    Based on the above, DeclarationStore should just manage set properties. If a
    shorthand is used and any of the values are omitted, the corresponding
    individual properties should be considered "unset" (tells the consumer to
    supply a desired default value).

    Property states:
        1) Use default value, not specified
        2) Use default value, set with specificity S (if a shorthand has been used but this property value was omitted)
        3) Specified value, set with specificity S

    Note that from the consumers point of view, 1) and 2) are identical ("unset"). These
    are only used by DeclarationStore to keep track of the specificity with
    which a "default value is set".

    Devise a system to facilitate parsing shorthand declarations into their corresponding individual properties.

    """

    __slots__ = ("_values", "_S")

    def __init__(self) -> None:
        # NOTE: a property may be in _S but not in _values, if the value is
        # "unset" by a shorthand. _S is completely internal, used only for
        # tracking the specificity of property values, set or unset alike.
        self._values: dict[str, Any] = dict()
        self._S: dict[str, int] = dict()

    def __getitem__(self, __key: Any) -> Any:
        if __key not in self._values:
            raise KeyError(__key)
        return self._values[__key]

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterator:
        return iter(self._values)

    def add(
        self,
        declarations: tinycss2.parser.Declaration
        | Iterable[tinycss2.parser.Declaration],
        *,
        inline: bool = False,
        specificity: Optional[tuple[int, int, int]] = None,
    ) -> None:
        """

        The `specificity` arg is (id, class, type) selectors

        The total specificity score is assigned as the sum of the following
            !important      10000
            inline          1000
            ID selector     100     (per selector)
            CLASS selector  10      (per selector)
            TYPE selector   1       (per selector)

        """

        s = 0
        if inline:
            s += 1000
        if specificity is not None:
            s += specificity[0] * 100 + specificity[1] * 10 + specificity[2]

        if not isinstance(declarations, (list, tuple, set)):
            declarations = [declarations]
        for decl in declarations:
            sc = s
            if decl.important:
                sc += 10000

            # TODO: Parse declaration into individual properties and associated values
            # Store properties and their values along with the corresponding specificity S.
            # If properties are already set, only update the value if S >= S0.
            # Property values are stored in _values. If a value is unset, remove entry in _values.
            # S values are stored in _S. These are never removed in the lifetime of the store.

            # name = decl.lower_name
            # if name not in self._decl:
            #     self._decl[name] = []
            # self._decl[name].append((decl, sc))


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

    def get_styles(
        self,
        element: etree.Element,
        fileprovider: FileProvider,
    ) -> Iterable[tinycss2.parser.AtRule | tinycss2.parser.QualifiedRule]:
        """Return the style rules from the element, if any.

        If the element links to another file, `fileprovider` should be used to
        get the file.
        """

    def get_node(
        self,
        element: etree.Element,
        styles: Optional[Styles] = None,
        children: Optional[list[Node]] = None,
    ) -> Node:
        """Return a Node instance if possible, otherwise raise UnsupportedElementError."""
        ...


class FileType(Enum):
    XML = "xml"
    XHTML = "xhtml"
    HTML = "html"
    CSS = "css"


class FileProvider(Protocol):
    def get_path(self, ref: str) -> str | Path:
        """Returns the path/url of the provided reference.

        Should raise FileNotFoundError if `ref` cannot be resolved/found.
        """

    def get_type(self, path: str | Path) -> FileType | None:
        """Returns the FileType of the provided filepath, or None if unrecognized."""

    def read_bytes(self, path: str | Path) -> tuple[bytes, str | None]:
        """Reads content of `path` resource and returns it as a tuple of the read bytes and the encoding (if available)."""

    def read_str(self, path: str | Path) -> str:
        """Reads content of `path` resource and returns it as a string."""


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
        parent = element.getparent()
        if parent is not None and parent.tag == "head":
            if element.tag == "style":
                return ElementType.STYLES
            if (
                element.tag == "link"
                and "rel" in element.attrib
                and element.attrib["rel"] == "stylesheet"
                and "type" in element.attrib
                and element.attrib["type"] == "text/css"
                and "href" in element.attrib
            ):
                return ElementType.STYLES
            return ElementType.UNSUPPORTED

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

        if self.get_type(element) != ElementType.STYLES:
            raise UnsupportedElementError("Element does not contain styles")

        if element.tag == "style":
            styles = element.text
        elif element.tag == "link":
            path = fileprovider.get_path(element.attrib["href"])
            if fileprovider.get_type(path) != FileType.CSS:
                return []
            styles = fileprovider.read_str(path)
        else:
            return []

        return tinycss2.parse_stylesheet(
            styles, skip_comments=True, skip_whitespace=True
        )

    def get_node(
        self,
        element: etree.Element,
        styles: Optional[Styles] = None,
        children: Optional[list[Node]] = None,
    ) -> Node:
        if element.tag not in ("body", "div"):
            raise UnsupportedElementError(
                "Only <body> and <div> elements are supported"
            )

        content = element.text
        if content is not None:
            content = content.strip()
        if content:
            raise UnsupportedElementError("Elements containing text are not supported")

        key = None
        for attr, value in element.attrib.items():
            match attr:
                case "style":
                    if styles is None:
                        styles = Styles()
                    styles.add(
                        tinycss2.parse_declaration_list(
                            value, skip_comments=True, skip_whitespace=True
                        ),
                        inline=True,
                    )
                case "id":
                    key = value
                case _:
                    logger.warn(
                        "Attribute '%s' ('%s') is unsupported and will be ignored",
                        attr,
                        value,
                    )

        # TODO: Create style
        # style = Style.from_props(styles)
        style = None
        if children is None:
            children = []
        return Node(*children, key=key, style=style)


class StandardFileProvider:
    """Standard implementation of FileProvider with no preprocessing of files."""

    __slots__ = "_basepath"

    def __init__(self, basefile: Optional[Path] = None) -> None:
        self._basepath = None

        if basefile is None:
            return

        if not isinstance(basefile, Path):
            basefile = Path(basefile)
        if not basefile.is_file or not basefile.exists():
            raise FileNotFoundError(
                "basefile must be a path to a valid and existing file"
            )
        self._basepath = basefile.parent

    @property
    def basepath(self) -> Path | None:
        return self._basepath

    def get_path(self, ref: str) -> str | Path:
        """Returns the path/url of the provided reference.

        Should raise FileNotFoundError if `ref` cannot be resolved/found.
        """

        path = Path(ref)
        if not path.is_absolute:
            # Use basepath to resolve if specified, otherwise it will be based
            # on current working directory
            if self.basepath:
                path = (self.basepath / path).resolve()
            else:
                path = path.absolute().resolve()

        if not path.exists():
            raise FileNotFoundError(path)

        return path

    def get_type(self, path: str | Path) -> FileType | None:
        """Returns the FileType of the provided filepath, or None if unrecognized."""
        if not isinstance(path, Path):
            path = Path(path)
        match path.suffix.casefold():
            case "xml":
                return FileType.XML
            case "xhtml":
                return FileType.XHTML
            case "html":
                return FileType.HTML
            case "css":
                return FileType.CSS
            case _:
                return None

    def read_bytes(self, path: str | Path) -> bytes:
        raise NotImplementedError

    def read_str(self, path: str | Path) -> str:
        with open(path, "r") as f:
            content = f.read()
        return content


def load(
    content: io.BytesIO | io.StringIO | Path | str | bytes,
    *,
    nodefactory: Optional[NodeFactory] = None,
    fileprovider: Optional[FileProvider] = None,
) -> Node:
    """Parse a string, bytes array or stream of an HTML/XML document into a node tree."""

    # TODO: Determine if content is XML/XHTML or HTML.
    # Keep in mind that `content` can be both a filepath, stream, etc.
    # Consider load_xml and load_html methods instead of inferring the type of content.
    # If <!DOCTYPE HTML ...> and/or <html> ... </html>, assume HTML, otherwise assume XML
    is_HTML = True

    if not nodefactory:
        if not is_HTML:
            raise ValueError("`nodefactory` is required for parsing XML")
        nodefactory = HTMLNodeFactory()

    if not fileprovider:
        basefile = (
            content
            if (
                isinstance(content, Path)
                or (isinstance(content, str) and Path.is_file(content))
            )
            else None
        )
        fileprovider = StandardFileProvider(basefile)

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

        # Get matching style declarations
        matches = matcher.match(element)
        if matches:
            styles = Styles()
            # 'order' (1) and 'pseudo' (2) are not supported, they are
            # ignored/discarded
            for specificity, _, _, decls in matches:
                styles.add(decls, specificity=specificity)
        else:
            styles = None

        # Create node
        return nodefactory.get_node(
            element.etree_element,
            styles,
            children,
        )

    return get_node(tree, is_root=True)
