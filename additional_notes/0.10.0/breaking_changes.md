### Dropping support for Qt5 backend

We started warning about this in release v0.8.0; it is now time to fully drop support of Qt5! Qt5 has reached End Of Life on the 26th of May 2025. We migrated our bundle to Qt6 (PySide6) a year ago.
[#9650](https://github.com/napari/napari/pull/9650) is effectively removing PyQt5 support. PySide2 support was already removed in release [0.7.0](https://github.com/napari/napari/pull/8450), so we are now fully on Qt6!

### Mouse callbacks fixes

Custom mouse callbacks can be [defined via generators](https://napari.org/stable/howtos/extending/connecting_events.html#listening-for-mouse-events). Some quirks with this machinery have been smoothed out and some bugs fixed ([#9513](https://github.com/napari/napari/pull/9513)); this might result in some callbacks to no longer work as before. In principle, this should only affect callbacks that relied on buggy behaviour, but please make sure to check if your old callbacks are still working, and open an issue on the napari repository if that's not the case.

A notable change is that `mouse_move` callbacks previously did not work during `drag`, but now they do. If that's not what you want, guard your callback with `if not event.is_dragging`!

### Removal of `scale_bar.unit`

After deprecating it, we're finally removing this field completely. Now the only way to set the unit on the scale bar is by [setting units on the layers themselves](https://napari.org/stable/guides/units.html#scale-and-units-live-on-layers)!
