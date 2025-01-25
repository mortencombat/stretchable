# New style parser

## Notes

...

## To-Do

[ ] style.parser
    [ ] Add tests for remaining CSS properties/value types
    [ ] Add remaining properties
        [ ] grid-template-rows
        [ ] grid-template-columns
        [ ] grid-auto-rows
        [ ] grid-auto-columns
        [ ] grid-row
        [ ] grid-column
    [ ] Consider if prefix should be supported by the base class
    [ ] Consider order of styles passed to from_decl
    [ ] Make prop arg for adapters and transformation to/from CSS name formats consistent between adapters
[ ] Implement Style._to_taffy()
[ ] Implement getting a shorthand property value? (eg. style["margin"] instead of fx style["margin-left"])
[ ] Add tests for remaining CSS properties/value types
[ ] Remove old code / cleanup
