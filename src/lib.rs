// #![feature(in_band_lifetimes)]
// #![feature(dec2flt)]

use std::f32;

extern crate dict_derive;
use dict_derive::{FromPyObject, IntoPyObject};

extern crate pyo3;
// use std::error::Error;

// use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::{wrap_pyfunction, wrap_pymodule};

extern crate taffy;
use taffy::prelude::*;

// use taffy::geometry::*;
// use taffy::node::*;
// use taffy::style::JustifyItems;
// use taffy::style::*;

// MAIN

#[pyfunction]
unsafe fn taffy_init() -> i64 {
    let taffy = Taffy::new();
    Box::into_raw(Box::new(taffy)) as i64
}

#[pyfunction]
unsafe fn taffy_free(taffy: i64) {
    let _ = Box::from_raw(taffy as *mut Taffy);
}

#[pyfunction]
unsafe fn taffy_enable_rounding(taffy: i64) {
    let mut taffy = Box::from_raw(taffy as *mut Taffy);
    taffy.enable_rounding();
    Box::leak(taffy);
}

#[pyfunction]
unsafe fn taffy_disable_rounding(taffy: i64) {
    let mut taffy = Box::from_raw(taffy as *mut Taffy);
    taffy.disable_rounding();
    Box::leak(taffy);
}

// STYLE

trait FromIndex<T> {
    fn from_index(index: i32) -> T;
}

trait FromIndexOptional<T> {
    fn from_index(index: Option<i32>) -> Option<T>;
}

impl FromIndex<Display> for Display {
    fn from_index(index: i32) -> Display {
        match index {
            0 => Display::None,
            1 => Display::Flex,
            2 => Display::Grid,
            _ => panic!("invalid index {}", index),
        }
    }
}

impl FromIndex<Position> for Position {
    fn from_index(index: i32) -> Position {
        match index {
            0 => Position::Relative,
            1 => Position::Absolute,
            _ => panic!("invalid index {}", index),
        }
    }
}

impl FromIndex<FlexWrap> for FlexWrap {
    fn from_index(index: i32) -> FlexWrap {
        match index {
            0 => FlexWrap::NoWrap,
            1 => FlexWrap::Wrap,
            2 => FlexWrap::WrapReverse,
            _ => panic!("invalid index {}", index),
        }
    }
}

impl FromIndex<FlexDirection> for FlexDirection {
    fn from_index(index: i32) -> FlexDirection {
        match index {
            0 => FlexDirection::Row,
            1 => FlexDirection::Column,
            2 => FlexDirection::RowReverse,
            3 => FlexDirection::ColumnReverse,
            _ => panic!("invalid index {}", index),
        }
    }
}

// AlignItems, JustifyItems, AlignSelf, JustifySelf
impl FromIndexOptional<AlignItems> for AlignItems {
    fn from_index(index: Option<i32>) -> Option<AlignItems> {
        match index {
            None => None,
            Some(n) => match n {
                0 => Some(AlignItems::Start),
                1 => Some(AlignItems::End),
                2 => Some(AlignItems::FlexStart),
                3 => Some(AlignItems::FlexEnd),
                4 => Some(AlignItems::Center),
                5 => Some(AlignItems::Baseline),
                6 => Some(AlignItems::Stretch),
                _ => panic!("invalid index {}", n),
            },
        }
    }
}

// AlignContent, JustifyContent
impl FromIndexOptional<AlignContent> for AlignContent {
    fn from_index(index: Option<i32>) -> Option<AlignContent> {
        match index {
            None => None,
            Some(n) => match n {
                0 => Some(AlignContent::Start),
                1 => Some(AlignContent::End),
                2 => Some(AlignContent::FlexStart),
                3 => Some(AlignContent::FlexEnd),
                4 => Some(AlignContent::Center),
                5 => Some(AlignContent::Stretch),
                6 => Some(AlignContent::SpaceBetween),
                7 => Some(AlignContent::SpaceEvenly),
                8 => Some(AlignContent::SpaceAround),
                _ => panic!("invalid index {}", n),
            },
        }
    }
}

impl FromIndex<GridAutoFlow> for GridAutoFlow {
    fn from_index(index: i32) -> GridAutoFlow {
        match index {
            0 => GridAutoFlow::Row,
            1 => GridAutoFlow::Column,
            2 => GridAutoFlow::RowDense,
            3 => GridAutoFlow::ColumnDense,
            _ => panic!("invalid index {}", index),
        }
    }
}

#[derive(FromPyObject, IntoPyObject)]
struct PyLength {
    dim: i32,
    value: f32,
}

impl From<PyLength> for Dimension {
    fn from(length: PyLength) -> Dimension {
        match length.dim {
            1 => Dimension::Points(length.value),
            2 => Dimension::Percent(length.value),
            _ => Dimension::Auto,
        }
    }
}

impl From<PyLength> for LengthPercentageAuto {
    fn from(length: PyLength) -> LengthPercentageAuto {
        match length.dim {
            1 => LengthPercentageAuto::Points(length.value),
            2 => LengthPercentageAuto::Percent(length.value),
            _ => LengthPercentageAuto::Auto,
        }
    }
}

impl From<PyLength> for LengthPercentage {
    fn from(length: PyLength) -> LengthPercentage {
        match length.dim {
            1 => LengthPercentage::Points(length.value),
            2 => LengthPercentage::Percent(length.value),
            _ => panic!("Length should be points or percent, not auto"),
        }
    }
}

#[derive(FromPyObject, IntoPyObject)]
pub struct PySize {
    width: PyLength,
    height: PyLength,
}

impl From<PySize> for Size<Dimension> {
    fn from(size: PySize) -> Size<Dimension> {
        Size {
            height: Dimension::from(size.height),
            width: Dimension::from(size.width),
        }
    }
}

impl From<PySize> for Size<LengthPercentage> {
    fn from(size: PySize) -> Size<LengthPercentage> {
        Size {
            height: LengthPercentage::from(size.height),
            width: LengthPercentage::from(size.width),
        }
    }
}

#[derive(FromPyObject, IntoPyObject)]
pub struct PyRect {
    left: PyLength,
    right: PyLength,
    top: PyLength,
    bottom: PyLength,
}

impl From<PyRect> for Rect<LengthPercentage> {
    fn from(rect: PyRect) -> Rect<LengthPercentage> {
        Rect {
            left: LengthPercentage::from(rect.left),
            right: LengthPercentage::from(rect.right),
            top: LengthPercentage::from(rect.top),
            bottom: LengthPercentage::from(rect.bottom),
        }
    }
}

impl From<PyRect> for Rect<LengthPercentageAuto> {
    fn from(rect: PyRect) -> Rect<LengthPercentageAuto> {
        Rect {
            left: LengthPercentageAuto::from(rect.left),
            right: LengthPercentageAuto::from(rect.right),
            top: LengthPercentageAuto::from(rect.top),
            bottom: LengthPercentageAuto::from(rect.bottom),
        }
    }
}

impl From<PyRect> for Rect<Dimension> {
    fn from(rect: PyRect) -> Rect<Dimension> {
        Rect {
            left: Dimension::from(rect.left),
            right: Dimension::from(rect.right),
            top: Dimension::from(rect.top),
            bottom: Dimension::from(rect.bottom),
        }
    }
}

#[derive(FromPyObject, IntoPyObject)]
pub struct PyGridIndex {
    kind: i8,
    value: i16,
}

impl From<PyGridIndex> for GridPlacement {
    fn from(grid_index: PyGridIndex) -> Self {
        match grid_index.kind {
            1 => Self::from_line_index(grid_index.value),
            2 => Self::from_span(grid_index.value as u16),
            _ => Self::Auto,
        }
    }
}

#[derive(FromPyObject, IntoPyObject)]
pub struct PyGridPlacement {
    start: PyGridIndex,
    end: PyGridIndex,
}

impl From<PyGridPlacement> for Line<GridPlacement> {
    fn from(grid_placement: PyGridPlacement) -> Self {
        Self {
            start: GridPlacement::from(grid_placement.start),
            end: GridPlacement::from(grid_placement.end),
        }
    }
}

#[pyfunction]
unsafe fn taffy_style_create(
    // Layout mode/strategy
    display: i32,
    // Position
    position: i32,
    inset: PyRect,
    // Alignment
    align_items: Option<i32>,
    justify_items: Option<i32>,
    align_self: Option<i32>,
    justify_self: Option<i32>,
    align_content: Option<i32>,
    justify_content: Option<i32>,
    gap: PySize,
    // Spacing
    margin: PyRect,
    border: PyRect,
    padding: PyRect,
    // Size
    size: PySize,
    min_size: PySize,
    max_size: PySize,
    aspect_ratio: Option<f32>,
    // Flex
    flex_wrap: i32,
    flex_direction: i32,
    flex_grow: f32,
    flex_shrink: f32,
    flex_basis: PyLength,
    // Grid
    grid_auto_flow: i32,
    grid_row: PyGridPlacement,
    grid_column: PyGridPlacement,
) -> PyResult<i64> {
    let ptr = Box::into_raw(Box::new(Style {
        // Layout mode/strategy
        display: Display::from_index(display),
        // Position
        position: Position::from_index(position),
        inset: Rect::from(inset),
        // Alignment
        align_items: AlignItems::from_index(align_items),
        justify_items: JustifyItems::from_index(justify_items),
        align_self: AlignSelf::from_index(align_self),
        justify_self: JustifySelf::from_index(justify_self),
        align_content: AlignContent::from_index(align_content),
        justify_content: JustifyContent::from_index(justify_content),
        gap: Size::from(gap),
        // Spacing
        margin: Rect::from(margin),
        border: Rect::from(border),
        padding: Rect::from(padding),
        // Size
        size: Size::from(size),
        min_size: Size::from(min_size),
        max_size: Size::from(max_size),
        aspect_ratio: aspect_ratio,
        // Flex
        flex_wrap: FlexWrap::from_index(flex_wrap),
        flex_direction: FlexDirection::from_index(flex_direction),
        flex_grow: flex_grow,
        flex_shrink: flex_shrink,
        flex_basis: Dimension::from(flex_basis),
        // Grid
        grid_auto_flow: GridAutoFlow::from_index(grid_auto_flow),
        grid_row: Line::from(grid_row),
        grid_column: Line::from(grid_column),
        ..Default::default()
    }));
    Ok(ptr as i64)
}

#[pyfunction]
unsafe fn taffy_style_drop(style: i64) {
    let _style = Box::from_raw(style as *mut Style);
}

// NODES

#[pyfunction]
unsafe fn taffy_node_create(taffy: i64, style: i64) -> i64 {
    let mut taffy = Box::from_raw(taffy as *mut Taffy);
    let style = Box::from_raw(style as *mut Style);
    let node = taffy.new_leaf(*style).unwrap();

    Box::leak(taffy);

    Box::into_raw(Box::new(node)) as i64
}

#[pyfunction]
unsafe fn taffy_node_add_child(taffy: i64, node: i64, child: i64) {
    let mut taffy = Box::from_raw(taffy as *mut Taffy);
    let node = Box::from_raw(node as *mut Node);
    let child = Box::from_raw(child as *mut Node);

    taffy.add_child(*node, *child).unwrap();

    Box::leak(taffy);
    Box::leak(node);
    Box::leak(child);
}

#[pyfunction]
unsafe fn taffy_node_drop(taffy: i64, node: i64) {
    // Remove a specific node from the tree and drop it
    let mut taffy = Box::from_raw(taffy as *mut Taffy);
    let node = Box::from_raw(node as *mut Node);

    _ = taffy.remove(*node);
    Box::leak(taffy);
}

#[pyfunction]
unsafe fn taffy_node_drop_all(taffy: i64) {
    // Drops all nodes in the tree
    let mut taffy = Box::from_raw(taffy as *mut Taffy);

    taffy.clear();
    Box::leak(taffy);
}

// MODULE

#[pymodule]
pub fn _bindings(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(taffy_init))?;
    m.add_wrapped(wrap_pyfunction!(taffy_free))?;
    m.add_wrapped(wrap_pyfunction!(taffy_node_create))?;
    m.add_wrapped(wrap_pyfunction!(taffy_node_drop))?;
    m.add_wrapped(wrap_pyfunction!(taffy_node_add_child))?;
    m.add_wrapped(wrap_pyfunction!(taffy_node_drop_all))?;
    m.add_wrapped(wrap_pyfunction!(taffy_style_create))?;
    m.add_wrapped(wrap_pyfunction!(taffy_style_drop))?;
    m.add_wrapped(wrap_pyfunction!(taffy_enable_rounding))?;
    m.add_wrapped(wrap_pyfunction!(taffy_disable_rounding))?;

    // enable_rounding
    // disable_rounding
    // m.add_wrapped(wrap_pyfunction!(stretch_node_set_measure))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_set_style))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_dirty))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_mark_dirty))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_replace_child_at_index))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_remove_child))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_remove_child_at_index))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_compute_layout))?;

    Ok(())
}

// for pyo3-pack, name must match module.
#[pymodule]
fn taffy(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pymodule!(_bindings))?;
    Ok(())
}
