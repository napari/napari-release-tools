### Define a startup script for custom launch behaviour
Do you have a code snippet that you always find yourself running after you launch napari? No more! You can now put this code in a script and set its path in the new `startup script` setting ([#8188](https://github.com/napari/napari/pull/8188)), and it will be executed every time napari opens. It's just a python script, so sky's the limit :) We found it particularly useful for adding custom colormaps, setting up the scale bar *just right*, or automatically launching our favourite plugin on startup.

TODO: image here

### Multilayer features table widget
If you have multiple layers with similar feature tables (such as points or shapes annotations from different processing pipelines), you may want to easily compare these features between different layers. Following up on the recent addition of the [Features Table Widget](features-table-widget), you can now select multiple layers while the widget is active, and their features tables will be automatically joined into a single table ([#8189](https://github.com/napari/napari/pull/8189))!

TODO: image here

### Automatically tiled overlays and ColorBar overlay
Canvas overlays such as `scale_bar`, `text_overlay`, and `color_bar` overlay are now automatically tiling ([#7836](https://github.com/napari/napari/pull/7836)), preventing annoying overlap and making them easier to use without having to manage positioning. Wait, `color_bar` overlay you said? You heard it right! This is a new overlay ([#7832](https://github.com/napari/napari/pull/7832))that shows a color bar legend, and it works with any layer which uses a colormap. All of this works seamlessly with multiple overlays and even grid mode:

```py
import napari

viewer = napari.Viewer()

# enable grid with stride 2 to get layers split two-by-two
viewer.grid.enabled = True
viewer.grid.stride = 2

# set the scale bar to gridded mode so it appears in each grid box
viewer.scale_bar.visible = True
viewer.scale_bar.gridded = True

layers = viewer.open_sample('napari', 'lily')

# enable color bars
for layer in layers:
    layer.color_bar.visible = True
```

TODO: image here

### Task manager will now try to save your unfinished work
We added a new task manager ([#8211](https://github.com/napari/napari/pull/8211)) which automatically register any running `thread_worker`, showing a confirmation dialog if you attempt to close napari while a task is running.

### New `remove()` and `pop()` methods for Points and Shapes
Points and Shapes can now be easily removed, not just added :P ([#8031](https://github.com/napari/napari/pull/8031) and [#8072](https://github.com/napari/napari/pull/8072)).

### A new and updated guide on napari Preferences
Our documentation on the napari Preferences has received a major overhaul! [Check it out here](preferences).

TODO: does this link work?
