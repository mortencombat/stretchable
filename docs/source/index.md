---
hide-toc: true
---

# stretchable

**stretchable** is a layout library for Python that enables context-agnostic layout operations using CSS Block, [CSS Grid](https://css-tricks.com/snippets/css/complete-guide-grid/) and [Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/). Possible uses include UI layouts, page layouts for reports, complex plotting layouts, etc.

It implements Python bindings for [Taffy](https://github.com/dioxuslabs/taffy), an implementation of **CSS Block**, **Flexbox** and **CSS Grid** layout algorithms written in [Rust](https://www.rust-lang.org/). It was originally based on [Stretch](https://vislyhq.github.io/stretch/) (hence the name), but has since migrated to use Taffy. It is multi-platform and there are distributions available for Windows, Linux and macOS.

## Getting Started

**stretchable** is a Python package [hosted on PyPI](https://pypi.org/project/stretchable/). It can be installed using [pip](https://pip.pypa.io/en/stable/):

```console
$ python -m pip install stretchable
```

These next steps will help you get started:

- {doc}`overview` will introduce you to the basic concepts and show you a simple example of **stretchable** in action.
- {doc}`layouts` will help you understand the concepts of how you can use CSS to layout blocks of content.
- {doc}`examples` will give you a tour of the features and how to use them.
- If at any point you get confused by some of the terminology, please check out the {doc}`glossary <glossary>`.

## Project Information

- [Source Code](https://github.com/mortencombat/stretchable) {octicon}`mark-github`
- [Bug/Issue Tracker](https://github.com/mortencombat/stretchable/issues) {octicon}`mark-github`
- [PyPI](https://pypi.org/project/stretchable/)
- [Contributing](https://github.com/mortencombat/stretchable#contribute) {octicon}`mark-github`
- {doc}`license`

---

```{toctree}
:hidden:
:maxdepth: 2

overview
layouts
examples
api
glossary
license
genindex
```
