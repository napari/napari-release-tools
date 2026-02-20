### Breaking Changes

#### Transition to npe2 plugin engine 🔌

In 0.6.0 we began the process of deprecating npe1 (napari-plugin-engine).
In all 0.6.x releases, npe1 plugins were automatically converted to npe2 by default,
and users could turn off the `use_npe2_adaptor` setting to continue using npe1 plugins
without auto-conversion.

In 0.7.0 this setting is being removed ([PR #8448](https://github.com/napari/napari/pull/8448)),
and plugins will *only* continue to function if
they can be auto-converted to npe2. Most plugins will be unaffected, but those that rely
on import-time behaviour may not work as expected. If a plugin is relying on import-time
behaviour, it may be able to replicate this using the new startup scripts functionality added
in 0.6.5 ([#8188](https://github.com/napari/napari/pull/8188)).

If you encounter conversion issues in a plugin you rely on, please contact the
plugin authors to encourage them to migrate their plugin to the npe2 system.

This change has been a long time coming, and it's allowed us to remove thousands
of lines of tangled and confusing legacy code. Now that we have, it's unleashed
the potential for massive improvements to file opening and saving in `napari`,
and exciting new features for our plugin infrastructure. Stay tuned!

For more details on this change and how it affects plugins, see the [detailed
guide](adapted-plugin-guide). If you are a plugin author and your plugin is not
yet npe2-compatible, please see our [npe2 migration
guide](npe2-migration-guide), and, if you encounter any issues, get in touch in
our [Plugins Zulip chat
channel](https://napari.zulipchat.com/#narrow/channel/309872-plugins) or by
coming to one of our [community meetings](meeting-schedule).

#### Negative axis labels? A real positive

If you've ever loaded data of mixed dimensionality in napari, like a TYX volume
alongside a YX segmentation, you may have noticed the default axis labels didn't
quite line up:

| axes   | 0 | 1 | 2 |
|--------|---|---|---|
| volume | 0 | 1 | 2 |
| segmt  |   | 0 | 1 |

That's because napari used 0-based indexing for its viewer axis labels, which breaks
down when layers have different numbers of dimensions. With
[#8565](https://github.com/napari/napari/pull/8565),
viewer axis labels now use negative indexing by default, just like Python's own indexing
semantics. The last axis is always `-1`, the second-to-last is always `-2`, and so on:

| axes   | 0  | 1  | 2  |
|--------|----|----|----|
| volume | -3 | -2 | -1 |
| segmt  |    | -2 | -1 |

This means axis labels stay consistent as you add or remove layers of different
dimensionality -- axis `-1` is always your last axis. This also fixes
a long-standing bug where axis labels could end up duplicated when mixing layers of
different dimensionality ([#6569](https://github.com/napari/napari/issues/6569)).

You'll notice this change in the dims slider labels, the axis overlay, and the dims
popup widget. If you already label your axes with your own names (e.g. `z`, `y`, `x`),
nothing's changed. For everyone else, we have consistency at last!


#### What's in an angle? The truth! Fixed camera angles 🎥

If you've ever set up the camera to take that perfect publication-worthy photo of
your data (and taken the time to query the camera angles), you may have noticed they seemed... off.
That's because they were! Very... off. This was due to a long-standing bug in how we calculated our
camera angles, fueled in part by some arcane vispy axis-swapping tomfoolery, and in part by napari's
starting position of `viewer.camera.angles = (0, 0, 90)`.

Good news! With [#8281](https://github.com/napari/napari/pull/8281), angles make sense again. The default camera angles are `(0, 0, 0)`, and they
move intuitively -- so `viewer.camera.angles = (0, 0, 10)` actually represents a 10 degree
rotation around the 0th dimension. What a time to be alive!

Old versions of napari:

![Image showing an old version of a napari viewer with a layer opened and its camera angle (10, 0, 0) displayed in the console.](https://github.com/user-attachments/assets/9ae2040c-36f7-4c4c-8ef8-140202d7ccda)

New and sane:

![Image showing the 0.7.0 napari viewer with a layer opened and its camera angle (10, 0, 0) displayed in the console. The layer is rotated 10 degrees in its first dimension](https://github.com/user-attachments/assets/6b972b46-5c3c-439a-8b0a-fe8a293224e5)

All rotations are now right-handed (counterclockwise when the axis points towards the viewer),
with automatic sign-flipping for flipped camera views. We've also removed the unwieldy to type
(and confusing to reason about) `quaternion2euler_degrees` in favour of scipy's `Rotation` class.

Now for the bad news... After many (and we do [mean](https://github.com/napari/napari/pull/8537)
[**many**](https://github.com/napari/napari/pull/8557)) attempts, we realized we couldn't
provide legacy conversion functions to get you to and from the original camera angles. Therefore,
this is a **breaking change**.

If you had scripts or notebooks setting up angles for screenshots, or if you've got workshop
materials or tutorials with preset angles, they'll need to be updated. Any existing code
using `viewer.camera.angles = (z, y, x)` will now produce a different view than before.

### New features & widgets

#### What's my metadata? Where's my metadata? `napari-metadata` to the rescue

With a lot of work from our community contributor, Carlos Mario Rodriguez Reza (@carlosmariorr), and
our venerable community manager Tim Monko (@TimMonko), `napari` now has a metadata viewing and editing plugin
included in our `napari[all]` installation and our bundle ([PR #8576](https://github.com/napari/napari/pull/8576)).

![Screenshot of napari displaying an image of neurons, with the napari-metadata Layer Metadata widget across the bottom of the viewer.](https://raw.githubusercontent.com/napari/napari-metadata/main/resources/horizontal-widget.png)

Open the `Layer metadata` widget from the `Plugins` menu and you can view File information, and view and edit Axes metadata such as
axis labels, translation and scale! You can also use the widget to copy specified metadata across to other layers.

Check out the [README](https://github.com/napari/napari-metadata) for some usage documentation, and feel
free to open an issue to request new features -- we're actively improving this plugin so, more to come!

#### (Layer) Features galore

Prior to 0.7.0, our Features table widget only supported showing individual selected layer features.

With [#8189](https://github.com/napari/napari/pull/8189), courtesy of our community
contributor Marcelo Zoccoler (@zoccoler), the widget will display
features of all selected layers! The layer's name is displayed in an additional column, so you
always know what you're looking at, and you can choose to display only the shared feature columns
across all layers. Pretty slick!

![GIF displaying the usage of the features table with multiple selected layers.](https://github.com/user-attachments/assets/e06fd403-ed03-4edd-9192-a4e287d25ff7)

#### Smarter new layer buttons - inheriting from selected layers

Prior to 0.7.0, creating a new layer Points, Shapes or Labels layer would give you a layer
with extent and dimensionality equal to the union of all currently open layers, and with
none of the other spatial information (scale, units, etc.) inherited.

Now, with [#8357](https://github.com/napari/napari/pull/8357) you can create a new Shapes
or Points layer (Labels coming soon!) that inherits from a selected layer
(or a combination of selected layers). If you have one layer selected,
your new layer will copy all spatial information from its ancestor, ready for annotating!
If you have multiple layers selected, only scale is copied.

If you wish to recover the original behavior, deselect all existing layers before creating your new layer.

[#8649](https://github.com/napari/napari/pull/8649) ensures this change is not invisible!
When you have layers selected, the Points and Shapes buttons will be highlighted. You
can also hover over the buttons to get details about the behaviour.

![GIF displaying the highlights on the Shapes and Points new layer buttons when one or more layers are selected in the layerlist](https://github.com/user-attachments/assets/dba88d45-baa9-47df-80e9-5c7b1f2a711d)

PS -- You can now also create these new layers from the `File -> New Layer` menu!

#### Better text overalys 🔡

With [#8236](https://github.com/napari/napari/pull/8236), we've not only refactored text overlays
so they're easier to implement, but we've also introduced two new long-requested overlays:
the layer name overlay, and an overlay for the current slice. Together, they make generating
publication-ready figures much easier!

![Image showing the napari viewer with two layers in grid mode. Each layer has its name displayed in the top left, and the current slice displayed in the bottom right.](https://github.com/user-attachments/assets/3c96b38d-44c1-432b-b294-aa9c0934a553)

Try it yourself:

```python
import napari
v = napari.Viewer()
v.grid.enabled = True
ll = v.open_sample('napari', 'cells3d')
for l in ll:
    l.name_overlay.visible = True
v.scale_bar.visible = True
v.scale_bar.gridded = True
v._overlays['current_slice'].visible = True
v._overlays['current_slice'].gridded = True
v.dims.axis_labels = ['z', 'y', 'x']
```

**Note**: the `v._overlays` attribute is still private as we're working out the best API.

### Rendering & display

#### More pixels to play with - texture tiling

Ever loaded a large 2D image in napari just to zoom in and feel like you're not
really getting a lot of bang for your pixel bucks? That's because we were
downsampling images that were too large to send the whole thing to the GPU.

Courtesy of our community contributor, Guillaume Witz (@guiwitz), and his PR for
texture tiling ([PR #8395](https://github.com/napari/napari/pull/8395)) 2D
images that exceed OpenGL's maximum texture size will be split into multiple
tiles, each small enough to fit on the GPU.

![Image with a screenshot of napari 0.6.6 on the left and napari 0.7.0 on the right displaying a DeCAM image of the Milky Way. The image on the left is pixelated, while the image on the right is displayed at full resolution.](https://github.com/user-attachments/assets/d0a115a8-49d5-432c-b561-f29fe9ac8116)

#### Points - any size you like 🟣

On macOS, the points layer has never been able to reach its full potential, as OpenGL
drivers limit the size of an individual marker to a certain number of screen pixels.

With [#8552](https://github.com/napari/napari/pull/8552) and the release of `vispy v0.16`,
this long-standing issue has finally been resolved. Across all operating systems, you can
make your points as big as you want!

This change has also propagated to the zoom behaviour on macOS -- points now zoom
proportionally to the data, rather than staying the same size in screen pixels.

Here's the behaviour pre 0.7.0:

![Video with a points layer on a grid of white squares. When zooming, the points stay the same size in screen pixels.](../_static/images/points_zoom_066.webm)

And now:

![Video with a points layer on a grid of white squares. When zooming, the points scale proportionally to the data.](../_static/images/points_zoom_070.webm)


### Performance

#### Grid mode -- bigger, better, faster 📈

If you've been playing with our new grid mode since 0.6.5, you
may have stumbled into performance issues when progressively adding
new layers to the viewer. Stumble no longer! Our grid mode is now wicked fast and buttery smooth 🧈.

We've also fixed some issues with mouse interactions and deleting
layers, so you can tile to your heart's content. Try it out:

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
    layer.colorbar.visible = True
```

#### Add & delete layers without delay

[#8479](https://github.com/napari/napari/pull/8479) and [#8443](https://github.com/napari/napari/pull/8443)
made a number of improvements to
our layer and overlay clean-up, addressing a number of issues with large numbers of layers
in the viewer - adding them, deleting them, and even closing the viewer is now snappy
and smooth!

#### Shapes layers -- select, zoom, delete, repeat

If you've ever tried working with thousands of shapes in napari, you'll know
it could get... painful. Selecting 10,000 shapes with a box took over 50 seconds,
deleting 5,000 shapes took over a minute, and zooming with shapes selected
would lock up the viewer entirely. Not anymore!

0.7.0 brings a flurry of performance improvements:

- Box selection now uses bounding boxes and vectorized intersection tests,
  delivering a more than 100x speedup ([#8378](https://github.com/napari/napari/pull/8378)).
  Selecting 10,000 shapes goes from >50s to ~0.3s.
- Batch deletion replaces one-by-one removal for another 100x speedup
  ([#8375](https://github.com/napari/napari/pull/8375))! Deleting 50,000 shapes
  now takes under half a second.
- Outline computation is batched and cached, so zooming and panning with
  selected shapes no longer blocks
  ([#8403](https://github.com/napari/napari/pull/8403),
  [#8536](https://github.com/napari/napari/pull/8536)).
- Highlight updates are throttled for large layers, enabling smooth zoom
  even with 200,000+ shapes ([#8404](https://github.com/napari/napari/pull/8404)).
- Mode switching no longer triggers unnecessary redraws, giving another
  ~3x speedup when many shapes are selected
  ([#8551](https://github.com/napari/napari/pull/8551)).

Beware: there's still more to do, because drawing and drag-moving large selections
remain slow!

### Infrastructure & dependencies

A couple of notes on big changes in our dependencies:

- With #8509 we improved our support for `pydantic v2`, allowing us to enable support for Python 3.14!
This brings us one step closer to fully adopting `psygnal` as our event library.
- In [#8450](https://github.com/napari/napari/pull/8450) we dropped support for PySide2. If you
were using napari with PySide for your Qt bindings, you'll need to upgrade to PySide6. Good news
is that PySide6 is looking pretty stable, while PySide2 had some compatibility issues with numpy2,
and had to be built from source for Python 3.11+.
- In ([#8665](https://github.com/napari/napari/pull/8665)) we updated the default qt
binding to PyQt6. PyQt6 will now be installed with `napari[all]` installations. Windows users
should see improvements to their display with better support for fractional scaling!
- In [#8338](https://github.com/napari/napari/pull/8338) we replaced `numpydoc` with `docstring_parser`
for parsing our docstrings. This will be a pretty invisible change from a user's perspective, but
it saves more than 50MB of disk space for a napari install!
