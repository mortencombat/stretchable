from __future__ import annotations

from enum import Enum
from typing import Any

from docutils.nodes import Element
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.domains import ObjType
from sphinx.domains.python import PyClasslike, PyXRefRole
from sphinx.environment import BuildEnvironment
from sphinx.ext.autodoc import ClassDocumenter, bool_option
from sphinx.util.inspect import memory_address_re


def setup(app: Sphinx) -> None:
    app.setup_extension("sphinx.ext.autodoc")  # Require autodoc extension

    app.registry.domains["py"].object_types["enum"] = ObjType("enum", "class", "obj")
    app.add_directive_to_domain("py", "enum", PyClasslike)
    app.add_role_to_domain("py", "enum", PyXRefRole())

    app.add_autodocumenter(EnumDocumenter)


class EnumDocumenter(ClassDocumenter):
    objtype = "enum"
    directivetype = "enum"
    priority = 20
    class_xref = ":class:`~enum.Enum`"

    # priority = 10 + ClassDocumenter.priority
    option_spec = dict(ClassDocumenter.option_spec)
    option_spec["hex"] = bool_option

    @classmethod
    def can_document_member(
        cls, member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        try:
            return issubclass(member, Enum)
        except TypeError:
            return False

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)
        # self.add_line("   :final:", self.get_sourcename())
        # self.add_line("   :final:", self.get_sourcename())

    def add_content(
        self,
        more_content: StringList | None,
    ) -> None:
        super().add_content(more_content)

        source_name = self.get_sourcename()
        enum_object: Enum = self.object
        use_hex = self.options.hex
        self.add_line("", source_name)

        self.add_line(":Members:", source_name)
        names = []
        for name, member in enum_object.__members__.items():
            names.append(name)

            # value = member.value
            # if use_hex:
            #     objrepr = hex(value)
            # else:
            #     objrepr = memory_address_re.sub("", repr(value)).replace("\n", " ")

            # self.add_line(f"   .. attribute:: {name}", source_name)
            # self.add_line(f"      :annotation: {objrepr}", source_name)

            #   **: {the_member_value}", source_name)
            # self.add_line("", source_name)

        self.add_line("   ``" + "``, ``".join(names) + "``", source_name)
        self.add_line("", source_name)


class PyEnumXRefRole(PyXRefRole):
    """
    XRefRole for Enum/Flag members.

    .. versionadded:: 0.4.0
    .. autosummary-widths:: 40/100
    """

    def process_link(
        self,
        env: BuildEnvironment,
        refnode: Element,
        has_explicit_title: bool,
        title: str,
        target: str,
    ) -> tuple[str, str]:
        """
        Called after parsing title and target text, and creating the reference node (given in ``refnode``).

        This method can alter the reference node and must return a new (or the same)
        ``(title, target)`` tuple.

        :param env:
        :param refnode:
        :param has_explicit_title:
        :param title:
        :param target:

        :rtype:

        .. latex:clearpage::
        """

        refnode["py:module"] = env.ref_context.get("py:module")
        refnode["py:class"] = env.ref_context.get("py:class")

        if not has_explicit_title:
            title = title.lstrip(".")  # only has a meaning for the target
            target = target.lstrip("~+")  # only has a meaning for the title
            # if the first character is a tilde, don't display the module/class
            # parts of the contents

            if title[0:1] == "~":
                title = ".".join(title[1:].split(".")[-2:])

            elif title[0:1] == "+":
                title = title[1:]
                dot = title.rfind(".")
                if dot != -1:
                    title = title[dot + 1 :]

        # if the first character is a dot, search more specific namespaces first
        # else search builtins first
        if target[0:1] == ".":
            target = target[1:]
            refnode["refspecific"] = True

        return title, target
