from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from enum import Enum, IntEnum, auto
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Optional, Protocol

import cssselect2
import tinycss2
import tinycss2.ast as ast
from lxml import etree

from . import style as stl
from .node import Node

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


"""
TODO:
- Streamline declaration handlers
- Implement factory/DI pattern for handler specification (support user-defined handlers)
- Implement Style.from_props(...), which uses Styles class and recognizes/parses tinycss2 tokens
"""


def _handle_rect(
    declaration: tinycss2.parser.Declaration,
) -> list[tuple[str, list[ast.Node] | None]]:
    values = split(declaration.value)
    match len(values):
        case 1:
            top = right = bottom = left = values[0]
        case 2:
            top = bottom = values[0]
            left = right = values[1]
        case 3:
            top = values[0]
            left = right = values[1]
            bottom = values[2]
        case 4:
            top, right, bottom, left = values
        case _:
            raise ValueError(f"Unrecognized value: {declaration.serialize()}")
    return [("top", top), ("right", right), ("bottom", bottom), ("left", left)]


def split(
    nodes: list[ast.Node], sep: ast.Node = ast.WhitespaceToken
) -> list[list[ast.Node]]:
    """Equivalent to str.strip() except it takes a single list and returns the
    list split into multiple lists by a specified (or default) separator."""
    r = []
    cur = []
    for v in nodes:
        if isinstance(v, sep):
            if cur:
                r.append(cur)
                cur = []
            continue
        cur.append(v)
    if cur:
        r.append(cur)
    return r


def strip(nodes: list[ast.Node]) -> list[ast.Node]:
    """Strips any leading and trailing WhitespaceTokens from the nodes."""
    return [v for v in nodes if not isinstance(v, ast.WhitespaceToken)]


class StyleProvider(ABC, Mapping):
    """
    Manages/determines the effective applied style for an element.

    Add style declarations using the `add()` method and retrieve style
    properties using the Mapping protocol.
    """

    @abstractmethod
    def add(
        self,
        declarations: tinycss2.parser.Declaration
        | Iterable[tinycss2.parser.Declaration],
        *,
        inline: bool = False,
        specificity: Optional[tuple[int, int, int]] = None,
    ) -> None:
        """Add declarations to be applied to the element styling."""

    @abstractmethod
    def get_style(self) -> stl.Style:
        """Returns a Style instance corresponding to the effective applied style."""


DeclarationHandler = Callable[
    [tinycss2.parser.Declaration], list[tuple[str, list[ast.Node] | None]]
]


class StandardStyleProvider(StyleProvider):
    """
    Manages/determines the effective applied style for an element.

    Add style declarations using the `add()` method and retrieve style
    properties using the Mapping protocol.

    Only properties that are set with the added declarations will be listed. The
    property values will provided as unprocessed token(s).
    """

    __slots__ = ("_values", "_S")

    DEFAULT_HANDLER: DeclarationHandler = lambda d: [(d.lower_name, strip(d.value))]
    HANDLERS: dict[str, DeclarationHandler] = {
        "inset": _handle_rect,
        "padding": _handle_rect,
        "margin": _handle_rect,
        # "border": ...,  # this is more completed because it can contain border-style and border-color as well
        "border-width": _handle_rect,
    }

    def __init__(self) -> None:
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
        """Add declarations to be applied to the element styling.

        The `specificity` arg is (ID, CLASS, TYPE) selectors.

        The total specificity score is assigned as the sum of the following
            !important      +10000
            inline           +1000
            ID selector       +100 (per selector)
            CLASS selector     +10 (per selector)
            TYPE selector       +1 (per selector)
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

            # Parse declaration into individual properties and associated values
            # Store properties and their values along with the corresponding specificity S.
            # If properties are already set, only update the value if S >= S0.
            # Property values are stored in _values. If a value is unset, remove entry in _values.
            # S values are stored in _S. These are never removed in the lifetime of the store.
            for name, value in (
                StandardStyleProvider.HANDLERS[decl.lower_name](decl)
                if decl.lower_name in StandardStyleProvider.HANDLERS
                else StandardStyleProvider.DEFAULT_HANDLER(decl)
            ):
                if name in self._S and sc < self._S[name]:
                    continue
                self._S[name] = sc
                if value is not None:
                    self._values[name] = value
                elif name in self._values:
                    del self._values[name]

    def get_style(self) -> stl.Style:
        """Returns a Style instance corresponding to the effective applied style."""
        return StandardStyleProvider._get_style(self)

    MAP_ENUMS: dict[str, IntEnum] = {
        "display": stl.Display,
        "flex-direction": stl.FlexDirection,
        "flex-wrap": stl.FlexWrap,
        "overflow": stl.Overflow,
        "align-items": stl.AlignItems,
        "align-self": stl.AlignSelf,
        "align-content": stl.AlignContent,
        "justify-items": stl.JustifyItems,
        "justify-self": stl.JustifySelf,
        "justify-content": stl.JustifyContent,
        "position": stl.Position,
        "grid-auto-flow": stl.GridAutoFlow,
    }

    @staticmethod
    def _get_style(
        props: Mapping[str, list[ast.Node]], *, ignore_unused_props: bool = False
    ) -> stl.Style:
        """The actual implementation, invoked by the instance variation of this
        method."""

        def get_length(
            node: ast.PercentageToken | ast.DimensionToken | ast.IdentToken,
        ) -> stl.Length:
            match node.type:
                case "percentage":
                    return stl.geometry.LengthPointsPercentAuto.percent(
                        float(node.representation) / 100
                    )
                case "dimension":
                    if node.lower_unit == "px":
                        return stl.geometry.LengthPointsPercentAuto.points(
                            float(node.representation)
                        )
                case "ident":
                    if node.lower_value == "auto":
                        return stl.geometry.LengthPointsPercentAuto.auto()

            raise ValueError(f"Unsupported or unrecognized value for length: {node}")

        def get_rects():
            for arg, prefix, suffix, default in (
                ("inset", "", "", stl.AUTO),
                ("padding", "padding-", "", 0),
                ("margin", "margin-", "", 0),
                ("border", "border-", "-width", 0),
            ):
                values = [default] * 4
                not_present = True
                for i, edge in enumerate(("top", "right", "bottom", "left")):
                    key = prefix + edge + suffix
                    if key not in keys:
                        continue
                    keys.remove(key)
                    v = strip(props[key])
                    if len(v) != 1:
                        raise ValueError(f"Invalid value for {key}: {v}")
                    values[i] = get_length(v[0])
                    not_present = False
                if not_present:
                    continue
                args[arg] = stl.Rect(*values)
                print(str(args[arg]))

        def get_sizes():
            for prefix in (None, "min", "max"):
                values = [stl.AUTO] * 2
                not_present = True
                for i, dim in enumerate(("width", "height")):
                    key = prefix + "-" + dim if prefix else dim
                    if key not in keys:
                        continue
                    keys.remove(key)
                    v = strip(props[key])
                    if len(v) != 1:
                        raise ValueError(f"Invalid value for {key}: {v}")
                    values[i] = get_length(v[0])
                    not_present = False
                if not_present:
                    continue
                key = prefix + "-size" if prefix else "size"
                args[key] = stl.Size(*values)
                print(str(args[key]))

        def get_enums():
            for key, enum in StandardStyleProvider.MAP_ENUMS.items():
                if key not in keys:
                    continue
                keys.remove(key)
                v = strip(props[key])
                # v should be a list with a single IdentToken, the value of which is
                # the property value (str).
                if (
                    not isinstance(v, list)
                    or len(v) != 1
                    or not isinstance(v[0], ast.IdentToken)
                ):
                    raise ValueError(f"Invalid value for {key}: {v}")

                args[key.replace("-", "_")] = enum[
                    v[0].value.strip().upper().replace("-", "_")
                ]

        def get_floats():
            for key in ("flex-basis", "flex-grow", "flex-shrink", "aspect-ratio"):
                if key not in keys:
                    continue
                keys.remove(key)
                v = strip(props[key])
                if (
                    key == "aspect-ratio"
                    and len(v) == 3
                    and isinstance(v[0], ast.NumberToken)
                    and isinstance(v[1], ast.LiteralToken)
                    and v[1].value == "/"
                    and isinstance(v[2], ast.NumberToken)
                    and float(v[2].value) > 0
                ):
                    # aspect-ratio on the form: width / height
                    v = float(v[0].value) / float(v[2].value)
                elif len(v) == 1 and isinstance(v[0], ast.NumberToken):
                    v = float(v[0].value)
                else:
                    raise ValueError(f"Invalid value for {key}: {v}")
                args[key.replace("-", "_")] = v

        # props is immutable. To track which properties have been used, create a
        # set with property names ('keys').
        args = dict()
        keys = set(props.keys())

        get_rects()
        get_sizes()
        get_enums()
        get_floats()
        # TODO: process remaining (supported) props

        if not ignore_unused_props and keys:
            logger.warning(
                f"Style properties not recognized or supported: {', '.join(keys)}"
            )

        print(args)

        return stl.Style(**args)


class NodeFactory(Protocol):
    def get_styleprovider(self) -> StyleProvider:
        """Return a new instance of the StyleProvider implementation to be used."""

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
        styles: Optional[StyleProvider] = None,
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

    def get_styleprovider(self) -> StyleProvider:
        return StandardStyleProvider()

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
        styles: Optional[StyleProvider] = None,
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
                        styles = self.get_styleprovider()
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

        print("get node for", element.tag)
        if styles:
            for name, value in styles.items():
                print(name, "=", value)

        if children is None:
            children = []
        return Node(*children, key=key, style=styles.get_style() if styles else None)


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
            styles = nodefactory.get_styleprovider()
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
