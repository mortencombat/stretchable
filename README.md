# stretchable

[![PyPI - Version](https://img.shields.io/pypi/v/stretchable)](https://pypi.org/project/stretchable/)
[![Python Versions](https://img.shields.io/pypi/pyversions/stretchable)](https://www.python.org)
[![License](https://img.shields.io/github/license/mortencombat/stretchable?color=blue)](https://github.com/mortencombat/stretchable/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/mortencombat/stretchable?logo=github)](https://github.com/mortencombat/stretchable/issues)
[![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/mortencombat/stretchable/build-publish.yml?logo=github)](https://github.com/mortencombat/stretchable/actions/workflows/build-publish.yml)
[![Documentation Status](https://readthedocs.org/projects/stretchable/badge/?version=latest)](https://stretchable.readthedocs.io/en/latest/?badge=latest)
[![Test results](https://gist.githubusercontent.com/mortencombat/901f1f1190ba5aff13164ede9d4c249f/raw/stretchable-tests.svg)](https://github.com/mortencombat/stretchable/actions/workflows/test.yml)
[![Test coverage](https://gist.githubusercontent.com/mortencombat/b121474745d15f92a295a0bdd7497529/raw/stretchable-coverage.svg)](https://github.com/mortencombat/stretchable/actions/workflows/test.yml)

**stretchable** is a layout library for Python that enables context-agnostic layout operations using CSS Block, [CSS Grid](https://css-tricks.com/snippets/css/complete-guide-grid/) and [Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/). Possible uses include UI layouts, page layouts for reports, complex plotting layouts, etc.

It implements Python bindings for [Taffy](https://github.com/dioxuslabs/taffy), an implementation of **CSS Block**, **Flexbox** and **CSS Grid** layout algorithms written in [Rust](https://www.rust-lang.org/). It was originally based on [Stretch](https://vislyhq.github.io/stretch/) (hence the name), but has since migrated to use Taffy. It is multi-platform and there are distributions available for Windows, Linux and macOS.

## Getting Started

**stretchable** is a Python package [hosted on PyPI](https://pypi.org/project/stretchable/). It can be installed using [pip](https://pip.pypa.io/en/stable/):

```console
python -m pip install stretchable
```

Building a tree of nodes and calculating the layout is as simple as:

```python
from stretchable import Edge, Node
from stretchable.style import AUTO, PCT

# Build node tree
root = Node(
    margin=20,
    size=(500, 300),
).add(
    Node(border=5, size=(50 * PCT, AUTO)),
    Node(key="child", padding=10 * PCT, size=50 * PCT),
)

# Compute layout
root.compute_layout()

# Get the second of the child nodes
child_node = root.find("/child")
content_box = child_node.get_box(Edge.CONTENT)
print(content_box)
# Box(x=300.0, y=50.0, width=150.0, height=50.0)

```

For more information and details, see the [documentation](https://stretchable.readthedocs.io/).

## Contributing

Contributions are welcomed. Please open an issue to clarify/plan implementation details prior to starting the work.

### Building

Install Rust with [rustup](https://rustup.rs/) and use `maturin develop` for development and `maturin build [--release]` to build.

### Documentation

To build documentation use `make html` (in `docs/` folder) or, to use live reloading: `sphinx-autobuild docs/source docs/build/html`

NOTE: Sometimes, you may need to run `make clean html` (in `docs/` folder) to ensure that all changes are included in the built html.

### Testing

Install test dependencies and invoke `pytest`. Note that there are ~900 tests, the majority of which are run using Selenium with the Chrome WebDriver, and the complete test suite can take ~30 minutes to complete. Use `pytest --lf` to only run the last-failed tests.

To run basic tests and ensure compatibility with a specific Python version, use Docker and the provided `Dockerfile`: `docker build . [--build-arg pyver=3.11]` (defaults to lowest supported Python version, currently 3.8).

## License

This work is released under the MIT license. A copy of the license is provided in the [LICENSE](https://github.com/mortencombat/stretchable/blob/main/LICENSE) file.
