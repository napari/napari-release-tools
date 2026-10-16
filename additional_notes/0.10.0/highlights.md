### Dropping support for Qt5 backend

We started warning about this in release v0.8.0; it is now time to fully drop support of Qt5! Qt5 has reached End Of Life on the 26th of May 2025. We migrated our bundle to Qt6 (PySide6) a year ago.
[#9650](https://github.com/napari/napari/pull/9650) is effectively removing PyQt5 support. PySide2 support was already removed in release [0.7.0](https://github.com/napari/napari/pull/8450), so we are now fully on Qt6!

### Grid Lines, axes and ticks
This features has been requested for years, and we finally managed to get a version that we're happy with! You can now use `viewer.scene.overlays.grid_lines` to display a grid on your data, including unit-aware tick marks and axis labels! Try it out:

```py
import napari

viewer = napari.Viewer(ndisplay=3)
layers = viewer.open_sample('napari', 'cells3d')

for layer in layers:
    layer.units = 'nm'
    layer.axis_labels = ['z', 'y', 'x']

viewer.scene.overlays.grid_lines.visible = True
```

![screenshot of the viewer with the grid_lines overlay enabled, showing the grid with axis labels and units, and axis ticks](https://github.com/user-attachments/assets/54993979-4774-4e66-87fb-d1bfcb27fb98)

### Colorful names

Another long-requested feature: displaying layer names on the canvas with colormap-aware colors ([#9598](https://github.com/napari/napari/pull/9598))! This comes with some fancy machinery to ensure that colors are shifted enough to be always readable.

```py
import napari

viewer = napari.Viewer()
layers = viewer.open_sample('napari', 'lily')

for layer in layers:
    layer.name_overlay.visible = True

viewer.canvas.grid.enabled = True
viewer.canvas.grid.stride = 2
```

![screenshot of the viewer with layer names overlays enabled, colored based on each layer's colormap](https://github.com/user-attachments/assets/629e63f5-381a-4a92-ba17-de02fa408edf)
