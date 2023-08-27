// #![feature(in_band_lifetimes)]
// #![feature(dec2flt)]

use std::f32;

// extern crate dict_derive;
// use dict_derive::{FromPyObject, IntoPyObject};

extern crate pyo3;
use pyo3::prelude::*;
use pyo3::{wrap_pyfunction, wrap_pymodule};
use pyo3::exceptions::PyValueError;

extern crate taffy;
use taffy::prelude::*;
// use taffy::geometry::*;
// use taffy::node::*;
// use taffy::style::*;

// region Enums

trait FromIndex<T> {
    fn from_index(index: i32) -> PyResult<T>;
}

impl FromIndex<AlignItems> for AlignItems {
    fn from_index(index: i32) -> PyResult<AlignItems> {
        match index {
            0 => Ok(AlignItems::Start),
            1 => Ok(AlignItems::End),
            2 => Ok(AlignItems::FlexStart),
            3 => Ok(AlignItems::FlexEnd),
            4 => Ok(AlignItems::Center),
            5 => Ok(AlignItems::Baseline),
            6 => Ok(AlignItems::Stretch),
            n => Err(PyValueError::new_err(format!("enum AlignItems - invalid index: {}", n))),
        }
    }
}


// endregion


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
unsafe fn taffy_style_create(
    align_items: i32,
    aspect_ratio: f32,
) -> PyResult<i64> {
    let ptr = Box::into_raw(Box::new(Style {
        align_items:     AlignItems::from_index(align_items)?,
        aspect_ratio: if f32::is_nan(aspect_ratio) { Number::Undefined } else { Number::Defined(aspect_ratio) },
    }));
    Ok(ptr as i64)
}

#[pyfunction]
unsafe fn taffy_style_drop(style: i64) {
    let _style = Box::from_raw(style as *mut Style);
}


#[pyfunction]
unsafe fn taffy_node_create(taffy: i64, style: i64) -> i64 {
    let mut taffy = Box::from_raw(taffy as *mut Taffy);
    let style = Box::from_raw(style as *mut Style);
    let node = taffy.new_leaf(*style).unwrap();

    Box::leak(style);
    Box::leak(taffy);

    Box::into_raw(Box::new(node)) as i64
}

#[pyfunction]
unsafe fn taffy_node_drop(taffy: i64, node: i64) {
    // Remove a specific node from the tree and drop it
    let mut taffy = Box::from_raw(taffy as *mut Taffy);
    let node = Box::from_raw(node as *mut Node);

    taffy.remove(*node);

    Box::leak(taffy);

    // Ok(node);
}

#[pyfunction]
unsafe fn taffy_nodes_clear(taffy: i64) {
    // Drops all nodes in the tree
    let mut taffy = Box::from_raw(taffy as *mut Taffy);

    taffy.clear();

    Box::leak(taffy);
}


// region Module

#[pymodule]
pub fn _bindings(_py: Python, m: &PyModule) -> PyResult<()> {
    /* FUNC*/
    m.add_wrapped(wrap_pyfunction!(taffy_init))?;
    m.add_wrapped(wrap_pyfunction!(taffy_free))?;
    m.add_wrapped(wrap_pyfunction!(taffy_node_create))?;
    m.add_wrapped(wrap_pyfunction!(taffy_node_drop))?;
    m.add_wrapped(wrap_pyfunction!(taffy_nodes_clear))?;
    m.add_wrapped(wrap_pyfunction!(taffy_style_create))?;
    m.add_wrapped(wrap_pyfunction!(taffy_style_drop))?;


    // m.add_wrapped(wrap_pyfunction!(stretch_style_create))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_style_free))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_create))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_free))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_set_measure))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_set_style))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_dirty))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_mark_dirty))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_add_child))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_replace_child_at_index))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_remove_child))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_remove_child_at_index))?;
    // m.add_wrapped(wrap_pyfunction!(stretch_node_compute_layout))?;
    /* END */
    Ok(())
}

// for pyo3-pack, name must match module.
#[pymodule]
fn taffy(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pymodule!(_bindings))?;
    Ok(())
}

// endregion