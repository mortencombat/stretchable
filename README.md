# Introduction

This package enables target-agnostic layout operations using the CSS flexbox algorithm. For instance, it can be used for page layouts in reporting tools, etc.

It implements Python bindings for [Stretch](https://vislyhq.github.io/stretch/), an implementation of Flexbox written in [Rust](https://www.rust-lang.org/). The project is based on the translation of the bindings from Swift to Python, from [stretched](https://github.com/nmichlo/stretched).

# Getting Started

Helpful resources to getting started with CSS Flexbox include:

- [A Complete Guide to Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [Flexbox Froggy](https://flexboxfroggy.com/)
- [Yoga Playground](https://yogalayout.com/playground)

# Usage

See [demos](https://github.com/mortencombat/stretchable/tree/main/demos) for examples of basic usage. Keep in mind that the current version of Stretchable is early stage and the API can be expected to change (eg. improve).

# Contributing

Install Rust with [rustup](https://rustup.rs/) and use `maturin build [--release]` to build.

# License

This work is released under the MIT license. A copy of the license is provided in the [LICENSE](https://github.com/mortencombat/stretchable/blob/main/LICENSE) file.
