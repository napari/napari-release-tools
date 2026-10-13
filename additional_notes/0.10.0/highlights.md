### Dropping support for Qt5 backend

We started warning about this in release v0.8.0; it is now time to fully drop support of Qt5! Qt5 has reached End Of Life on the 26th of May 2025. We migrated our bundle to Qt6 (PySide6) a year ago.
[#9650](https://github.com/napari/napari/pull/9650) is effectively removing PyQt5 support. PySide2 support was already removed in release [0.7.0](https://github.com/napari/napari/pull/8450), so we are now fully on Qt6!

### Colorful names

A long-requested feature: displaying layer names on the canvas with colormap-aware colors ([#9598](https://github.com/napari/napari/pull/9598))! This comes with some fancy machinery to ensure that colors are shifted enough to be always readable.

![screenshot of the viewer with layer names overlays enabled, colored based on each layer's colormap](https://github.com/user-attachments/assets/629e63f5-381a-4a92-ba17-de02fa408edf)
