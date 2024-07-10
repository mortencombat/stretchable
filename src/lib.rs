// #![feature(in_band_lifetimes)]
// #![feature(dec2flt)]

use core::panic;
// use std::fmt;
use log::{error, LevelFilter};
use taffy::Overflow;
use std::f32;

extern crate dict_derive;
use dict_derive::{FromPyObject, IntoPyObject};

extern crate pyo3;
// use pyo3::create_exception;
// use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

extern crate pyo3_log;
use pyo3_log::{Caching, Logger};

extern crate taffy;
// use taffy::node::MeasureFunc;
use taffy::prelude::*;

// MAIN

#[pyfunction]
fn init() -> usize {
    let taffy: TaffyTree<NodeContext> = TaffyTree::new();
    Box::into_raw(Box::new(taffy)) as usize
}

#[pyfunction]
fn free(taffy_ptr: usize) {
    let _ = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
}

#[pyfunction]
fn enable_rounding(taffy_ptr: usize) {
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
    taffy.enable_rounding();
    Box::leak(taffy);
}

#[pyfunction]
fn disable_rounding(taffy_ptr: usize) {
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
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
            3 => Display::Block,
            _ => panic!("invalid index {}", index),
        }
    }
}

impl FromIndex<Overflow> for Overflow {
    fn from_index(index: i32) -> Overflow {
        match index {
            0 => Overflow::Visible,
            1 => Overflow::Hidden,
            2 => Overflow::Scroll,
            3 => Overflow::Clip,
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

impl Into<PyLength> for AvailableSpace {
    fn into(self: AvailableSpace) -> PyLength {
        match self {
            AvailableSpace::Definite(value) => PyLength {
                dim: 1,
                value: value,
            },
            AvailableSpace::MinContent => PyLength { dim: 3, value: 0. },
            AvailableSpace::MaxContent => PyLength { dim: 4, value: 0. },
        }
    }
}

impl From<PyLength> for Dimension {
    fn from(length: PyLength) -> Dimension {
        match length.dim {
            0 => Dimension::Auto,
            1 => Dimension::Length(length.value),
            2 => Dimension::Percent(length.value),
            _ => panic!("unsupported dimension {}", length.dim),
        }
    }
}

impl From<PyLength> for AvailableSpace {
    fn from(length: PyLength) -> Self {
        match length.dim {
            1 => AvailableSpace::Definite(length.value),
            3 => AvailableSpace::MinContent,
            4 => AvailableSpace::MaxContent,
            _ => panic!("unsupported dimension {}", length.dim),
        }
    }
}

impl From<PyLength> for LengthPercentageAuto {
    fn from(length: PyLength) -> LengthPercentageAuto {
        match length.dim {
            0 => LengthPercentageAuto::Auto,
            1 => LengthPercentageAuto::Length(length.value),
            2 => LengthPercentageAuto::Percent(length.value),
            _ => panic!("unsupported dimension {}", length.dim),
        }
    }
}

impl From<PyLength> for LengthPercentage {
    fn from(length: PyLength) -> LengthPercentage {
        match length.dim {
            1 => LengthPercentage::Length(length.value),
            2 => LengthPercentage::Percent(length.value),
            _ => panic!("unsupported dimension {}", length.dim),
        }
    }
}

#[derive(FromPyObject, IntoPyObject)]
pub struct PySize {
    width: PyLength,
    height: PyLength,
}

impl From<PySize> for Size<Dimension> {
    fn from(size: PySize) -> Self {
        Size {
            height: Dimension::from(size.height),
            width: Dimension::from(size.width),
        }
    }
}

impl From<PySize> for Size<LengthPercentage> {
    fn from(size: PySize) -> Self {
        Size {
            height: LengthPercentage::from(size.height),
            width: LengthPercentage::from(size.width),
        }
    }
}

impl From<PySize> for Size<AvailableSpace> {
    fn from(size: PySize) -> Self {
        Size {
            height: AvailableSpace::from(size.height),
            width: AvailableSpace::from(size.width),
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

#[derive(FromPyObject, IntoPyObject)]
pub struct PyGridTrackSize {
    min_size: PyLength,
    max_size: PyLength,
}

impl From<PyGridTrackSize> for NonRepeatedTrackSizingFunction {
    fn from(size: PyGridTrackSize) -> NonRepeatedTrackSizingFunction {
        NonRepeatedTrackSizingFunction {
            min: MinTrackSizingFunction::from(size.min_size),
            max: MaxTrackSizingFunction::from(size.max_size),
        }
    }
}

impl FromIndex<GridTrackRepetition> for GridTrackRepetition {
    fn from_index(index: i32) -> GridTrackRepetition {
        if index == -1 {
            GridTrackRepetition::AutoFit
        } else if index == 0 {
            GridTrackRepetition::AutoFill
        } else if index > 0 {
            GridTrackRepetition::Count(index as u16)
        } else {
            panic!("invalid index {}", index)
        }
    }
}

#[derive(FromPyObject, IntoPyObject)]
pub struct PyGridTrackSizing {
    repetition: i32,
    single: Option<PyGridTrackSize>,
    repeat: Vec<PyGridTrackSize>,
}

impl From<PyGridTrackSizing> for TrackSizingFunction {
    fn from(value: PyGridTrackSizing) -> TrackSizingFunction {
        if value.repetition == -2 {
            TrackSizingFunction::Single(NonRepeatedTrackSizingFunction::from(value.single.unwrap()))
        } else {
            TrackSizingFunction::Repeat(
                GridTrackRepetition::from_index(value.repetition),
                value
                    .repeat
                    .into_iter()
                    .map(|e| NonRepeatedTrackSizingFunction::from(e))
                    .collect(),
            )
        }
    }
}

impl From<PyLength> for MinTrackSizingFunction {
    fn from(length: PyLength) -> MinTrackSizingFunction {
        match length.dim {
            0 => MinTrackSizingFunction::Auto,
            1 => MinTrackSizingFunction::Fixed(LengthPercentage::Length(length.value)),
            2 => MinTrackSizingFunction::Fixed(LengthPercentage::Percent(length.value)),
            3 => MinTrackSizingFunction::MinContent,
            4 => MinTrackSizingFunction::MaxContent,
            _ => panic!("unsupported dimension {}", length.dim),
        }
    }
}

impl From<PyLength> for MaxTrackSizingFunction {
    fn from(length: PyLength) -> MaxTrackSizingFunction {
        match length.dim {
            0 => MaxTrackSizingFunction::Auto,
            1 => MaxTrackSizingFunction::Fixed(LengthPercentage::Length(length.value)),
            2 => MaxTrackSizingFunction::Fixed(LengthPercentage::Percent(length.value)),
            3 => MaxTrackSizingFunction::MinContent,
            4 => MaxTrackSizingFunction::MaxContent,
            5 => MaxTrackSizingFunction::FitContent(LengthPercentage::Length(length.value)),
            6 => MaxTrackSizingFunction::FitContent(LengthPercentage::Percent(length.value)),
            7 => MaxTrackSizingFunction::Fraction(length.value),
            _ => panic!("unsupported dimension {}", length.dim),
        }
    }
}

#[pyfunction]
fn style_drop(style_ptr: usize) {
    let _style = unsafe { Box::from_raw(style_ptr as *mut Style) };
}

#[pyfunction]
fn style_create(
    // Layout mode/strategy
    display: i32,
    // Overflow
    overflow_x: i32,
    overflow_y: i32,
    scrollbar_width: f32,
    // Position
    position: i32,
    inset: PyRect,
    // Alignment
    gap: PySize,
    // Spacing
    margin: PyRect,
    border: PyRect,
    padding: PyRect,
    // Size
    size: PySize,
    min_size: PySize,
    max_size: PySize,
    // Flex
    flex_wrap: i32,
    flex_direction: i32,
    flex_grow: f32,
    flex_shrink: f32,
    flex_basis: PyLength,
    // Grid container properties
    grid_template_rows: Vec<PyGridTrackSizing>,
    grid_template_columns: Vec<PyGridTrackSizing>,
    grid_auto_rows: Vec<PyGridTrackSize>,
    grid_auto_columns: Vec<PyGridTrackSize>,
    grid_auto_flow: i32,
    // Grid child properties
    grid_row: PyGridPlacement,
    grid_column: PyGridPlacement,
    // Size, optional
    aspect_ratio: Option<f32>,
    // Alignment, optional
    align_items: Option<i32>,
    justify_items: Option<i32>,
    align_self: Option<i32>,
    justify_self: Option<i32>,
    align_content: Option<i32>,
    justify_content: Option<i32>,
) -> usize {
    let style = Style {
        // Layout mode/strategy
        display: Display::from_index(display),
        // Overflow
        overflow: taffy::geometry::Point { x: Overflow::from_index(overflow_x), y: Overflow::from_index(overflow_y)},
        scrollbar_width: scrollbar_width,
        // Position
        position: Position::from_index(position),
        inset: Rect::from(inset) as Rect<LengthPercentageAuto>,
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
        // Grid container properties
        grid_template_rows: grid_template_rows
            .into_iter()
            .map(|e| TrackSizingFunction::from(e))
            .collect(),
        grid_template_columns: grid_template_columns
            .into_iter()
            .map(|e| TrackSizingFunction::from(e))
            .collect(),
        grid_auto_rows: grid_auto_rows
            .into_iter()
            .map(|e| NonRepeatedTrackSizingFunction::from(e))
            .collect(),
        grid_auto_columns: grid_auto_columns
            .into_iter()
            .map(|e| NonRepeatedTrackSizingFunction::from(e))
            .collect(),
        grid_auto_flow: GridAutoFlow::from_index(grid_auto_flow),
        // Grid child properties
        grid_row: Line::from(grid_row),
        grid_column: Line::from(grid_column),
        ..Default::default()
    };
    Box::into_raw(Box::new(style)) as usize
}

// NODES

#[pyfunction]
fn node_create(taffy_ptr: usize, style_ptr: usize) -> usize {
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree<NodeContext>) };
    let style = unsafe { Box::from_raw(style_ptr as *mut Style) };
    // let node = taffy.new_leaf(*style.clone()).unwrap();
    let node = taffy.new_leaf_with_context(*style.clone(), NodeContext { node_id: 5 }).unwrap();

    Box::leak(style);
    Box::leak(taffy);

    Box::into_raw(Box::new(node)) as usize
}

#[pyfunction]
unsafe fn node_add_child(taffy_ptr: usize, node_ptr: usize, child_ptr: usize) {
    let mut taffy = Box::from_raw(taffy_ptr as *mut TaffyTree);
    let node = Box::from_raw(node_ptr as *mut NodeId);
    let child = Box::from_raw(child_ptr as *mut NodeId);

    taffy.add_child(*node, *child).unwrap();

    Box::leak(taffy);
    Box::leak(node);
    Box::leak(child);
}

#[pyfunction]
fn node_drop(taffy_ptr: usize, node_ptr: usize) {
    // Remove a specific node from the tree and drop it
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
    let node = unsafe { Box::from_raw(node_ptr as *mut NodeId) };

    _ = taffy.remove(*node);
    Box::leak(taffy);
}

#[pyfunction]
fn node_drop_all(taffy_ptr: usize) {
    // Drops all nodes in the tree
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };

    taffy.clear();
    Box::leak(taffy);
}

#[pyfunction]
fn node_replace_child_at_index(taffy_ptr: usize, node_ptr: usize, index: usize, child_ptr: usize) {
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
    let node = unsafe { Box::from_raw(node_ptr as *mut NodeId) };
    let child = unsafe { Box::from_raw(child_ptr as *mut NodeId) };

    taffy.replace_child_at_index(*node, index, *child).unwrap();

    Box::leak(taffy);
    Box::leak(node);
    Box::leak(child);
}

#[pyfunction]
fn node_remove_child(taffy_ptr: usize, node_ptr: usize, child_ptr: usize) {
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
    let node = unsafe { Box::from_raw(node_ptr as *mut NodeId) };
    let child = unsafe { Box::from_raw(child_ptr as *mut NodeId) };

    // TODO: this fails with an unknown error...
    taffy.remove_child(*node, *child).unwrap();

    Box::leak(taffy);
    Box::leak(node);
    Box::leak(child);
}

#[pyfunction]
fn node_remove_child_at_index(taffy_ptr: usize, node_ptr: usize, index: usize) {
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
    let node = unsafe { Box::from_raw(node_ptr as *mut NodeId) };

    taffy.remove_child_at_index(*node, index).unwrap();

    Box::leak(taffy);
    Box::leak(node);
}

#[pyfunction]
fn node_dirty(taffy_ptr: usize, node_ptr: usize) -> bool {
    let taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
    let node = unsafe { Box::from_raw(node_ptr as *mut NodeId) };
    let dirty = taffy.dirty(*node).unwrap();

    Box::leak(taffy);
    Box::leak(node);

    dirty
}

#[pyfunction]
fn node_mark_dirty(taffy_ptr: usize, node_ptr: usize) {
    let mut taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
    let node = unsafe { Box::from_raw(node_ptr as *mut NodeId) };

    taffy.mark_dirty(*node).unwrap();

    Box::leak(taffy);
    Box::leak(node);
}

#[pyfunction]
unsafe fn node_set_style(taffy: i64, node: i64, style: i64) {
    let mut taffy = Box::from_raw(taffy as *mut TaffyTree<NodeContext>);
    let node = Box::from_raw(node as *mut NodeId);
    let style = Box::from_raw(style as *mut Style);

    taffy.set_style(*node, *style).unwrap();

    Box::leak(taffy);
    Box::leak(node);
    // Box::leak(style);
}

#[pyfunction]
unsafe fn node_set_context(taffy: i64, node: i64, context: Option<u64>) {
    let mut taffy = Box::from_raw(taffy as *mut TaffyTree<NodeContext>);
    let node = Box::from_raw(node as *mut NodeId);

    taffy.set_node_context(
        *node, 
        match context {
            None => None,
            Some(context) => Some(NodeContext { node_id: context }),
        }
    ).unwrap();

    Box::leak(taffy);
    Box::leak(node);
}

#[pyfunction]
fn node_compute_layout(taffy: usize, node: usize, available_space: PySize) -> bool {
    let mut taffy = unsafe { Box::from_raw(taffy as *mut TaffyTree) };
    let node = unsafe { Box::from_raw(node as *mut NodeId) };
    
    let result = taffy.compute_layout(*node, Size::from(available_space));

    Box::leak(taffy);
    Box::leak(node);

    result.is_ok()
}

struct NodeContext {
    pub node_id: u64,
}

fn measure_function(
    known_dimensions: taffy::geometry::Size<Option<f32>>,
    available_space: taffy::geometry::Size<taffy::style::AvailableSpace>,
    node_context: Option<&mut NodeContext>,
    measure_callback: PyObject,
) -> Size<f32> {
    if let Size { width: Some(width), height: Some(height) } = known_dimensions {
        return Size { width, height };
    }

    if node_context.is_none() {
        return Size::ZERO;
    }

    // acquire lock
    let size = Python::with_gil(|py| -> Vec<f32> {
        // call function
        let available_width: PyLength = available_space.width.into();
        let available_height: PyLength = available_space.height.into();
        let args = (
            known_dimensions.width.unwrap_or(f32::NAN),
            known_dimensions.height.unwrap_or(f32::NAN),
            available_width,
            available_height,
            node_context.unwrap().node_id,
        );
        let result = measure_callback.call1(py, args);

        match result {
            Ok(result) => result.extract(py).unwrap(),
            Err(err) => {
                let traceback = match err.traceback(py) {
                    Some(value) => match value.format() {
                        Ok(tb) => format!("{}\n", tb),
                        Err(_) => String::new(),
                    },
                    None => String::new(),
                };
                error!(target: "stretchable.taffylib", "Error in node `measure` (used `NAN, NAN` in place):\n{}{}", traceback, err);
                vec![f32::NAN, f32::NAN]
            }
        }
    });

    // return result
    Size {
        width: size[0],
        height: size[1],
    }
    
}

#[pyfunction]
fn node_compute_layout_with_measure(taffy: usize, node: usize, available_space: PySize, measure: PyObject) -> bool {
    let mut taffy = unsafe { Box::from_raw(taffy as *mut TaffyTree<NodeContext>) };
    let node = unsafe { Box::from_raw(node as *mut NodeId) };

    let result = taffy.compute_layout_with_measure(
        *node, 
        Size::from(available_space), 
        |known_dimensions, available_space, _node_id, node_context, _style| {
            measure_function(known_dimensions, available_space, node_context, measure.clone())
        },
    );

    Box::leak(taffy);
    Box::leak(node);

    result.is_ok()
}

#[derive(FromPyObject, IntoPyObject)]
pub struct PyLayout {
    order: i64,
    location: Vec<f32>,
    size: Vec<f32>,
    content_size: Vec<f32>,
    scrollbar_size: Vec<f32>,
    border: Vec<f32>,
    padding: Vec<f32>,
    // margin: Vec<f32>,
}

trait FromPoint<T> {
    fn from_point(value: taffy::geometry::Point<T>) -> Vec<T>;
}

impl<T> FromPoint<T> for Vec<T> {
    fn from_point(value: taffy::geometry::Point<T>) -> Self {
        vec![ value.x, value.y ]
    }
}


trait FromSize<T> {
    fn from_size(value: taffy::geometry::Size<T>) -> Vec<T>;
}

impl<T> FromSize<T> for Vec<T> {
    fn from_size(value: taffy::geometry::Size<T>) -> Self {
        vec![ value.width, value.height ]
    }
}


trait FromRect<T> {
    fn from_rect(value: taffy::geometry::Rect<T>) -> Vec<T>;
}

impl<T> FromRect<T> for Vec<T> {
    fn from_rect(value: taffy::geometry::Rect<T>) -> Self {
        vec![ value.top, value.right, value.bottom, value.left ]
    }
}


impl From<Layout> for PyLayout {
    fn from(layout: Layout) -> Self {
        PyLayout {
            order: layout.order as i64,
            location: Vec::from_point(layout.location),            
            size: Vec::from_size(layout.size),            
            content_size: Vec::from_size(layout.content_size),            
            scrollbar_size: Vec::from_size(layout.scrollbar_size),
            border: Vec::from_rect(layout.border),  
            padding: Vec::from_rect(layout.padding),  
            // margin: Vec::from_rect(layout.margin),  
        }
    }
}

#[pyfunction]
fn node_get_layout(taffy_ptr: usize, node_ptr: usize) -> PyLayout {
    let taffy = unsafe { Box::from_raw(taffy_ptr as *mut TaffyTree) };
    let node = unsafe { Box::from_raw(node_ptr as *mut NodeId) };
    let layout = PyLayout::from(*taffy.layout(*node).unwrap());

    Box::leak(taffy);
    Box::leak(node);

    layout
}

// MODULE

// for pyo3-pack, name must match module.
#[pymodule]
fn taffylib(py: Python, m: &PyModule) -> PyResult<()> {
    Logger::new(py, Caching::LoggersAndLevels)?
        .filter(LevelFilter::Warn)
        // .filter_target("stretchable::taffylib".to_owned(), LevelFilter::Warn)
        .install()
        .unwrap();

    m.add_wrapped(wrap_pyfunction!(init))?;
    m.add_wrapped(wrap_pyfunction!(free))?;
    m.add_wrapped(wrap_pyfunction!(enable_rounding))?;
    m.add_wrapped(wrap_pyfunction!(disable_rounding))?;
    m.add_wrapped(wrap_pyfunction!(style_create))?;
    m.add_wrapped(wrap_pyfunction!(style_drop))?;
    m.add_wrapped(wrap_pyfunction!(node_create))?;
    m.add_wrapped(wrap_pyfunction!(node_drop))?;
    m.add_wrapped(wrap_pyfunction!(node_drop_all))?;
    m.add_wrapped(wrap_pyfunction!(node_add_child))?;
    m.add_wrapped(wrap_pyfunction!(node_replace_child_at_index))?;
    m.add_wrapped(wrap_pyfunction!(node_remove_child))?;
    m.add_wrapped(wrap_pyfunction!(node_remove_child_at_index))?;
    m.add_wrapped(wrap_pyfunction!(node_dirty))?;
    m.add_wrapped(wrap_pyfunction!(node_mark_dirty))?;
    m.add_wrapped(wrap_pyfunction!(node_set_style))?;
    m.add_wrapped(wrap_pyfunction!(node_get_layout))?;
    m.add_wrapped(wrap_pyfunction!(node_set_context))?;
    m.add_wrapped(wrap_pyfunction!(node_compute_layout))?;
    m.add_wrapped(wrap_pyfunction!(node_compute_layout_with_measure))?;

    Ok(())
}
