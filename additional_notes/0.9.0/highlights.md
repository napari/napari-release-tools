### Fuzzy find in command palette

Implement fuzzy find for the command palette ([#8661](https://github.com/napari/napari/pull/8661))

### Adjust grid rendering with hidden layers

If using grid layout without using stride, there are no blanks fields for hidden layers
thanks to [#9244](https://github.com/napari/napari/pull/9244)

### Inherit axis labels from layers

Thanks to [#9282](https://github.com/napari/napari/pull/9282) the axis labels in interface, next to slide and `Dims.axis_labels`
are calculated based on axis labels of layers

### Status bar coordinates as floats

Thanks to [#9287](https://github.com/napari/napari/pull/9287) we no longer render coordinates on scale bar
as integers, but as floats. It is important for all who use fractional
`Layer.scale`

### Public API for auto contrast limit

In [#9271](https://github.com/napari/napari/pull/9271) the public API for auto contrast limits is added



- Canvas model ([#8633](https://github.com/napari/napari/pull/8633))
- Implement Surface slicing with async request/response ([#8783](https://github.com/napari/napari/pull/8783))
- Remove translations code ([#8935](https://github.com/napari/napari/pull/8935))
- Add builtin Wavefront OBJ to surfaces reader ([#9228](https://github.com/napari/napari/pull/9228))
