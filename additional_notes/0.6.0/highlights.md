# What's new in napari 0.6.0

This note explains the new features and changes in napari 0.6.0.

For full details, see the changelog.

*Note Prerelease users should be aware that this document is currently in draft form. It will be updated substantially as napari 0.6.0 moves towards release, so it’s worth checking back even after reading earlier versions.*

## Summary - release highlights

- Updated viewer handedness ✋
- Display polygons with holes
- New command pallette 🎨
- Transition to npe2 plugin engine

## New features

### Updated viewer handedness ✋

So. Funny story. 😅

For (checks notes) 5 years or so, napari has had a 3D view, and for those 5
years, for almost all datasets, that view has been a *mirror image* of the 3D
object they were trying to represent. Any biologists among you might have
noticed that loading 3D molecular coordinates of DNA would result in a
left-handed helix, while anatomists among you might have been surprised by how
many of your samples suffered from [situs inversus
totalis](https://en.wikipedia.org/wiki/Situs_inversus)!

By and large, many things that people care about work exactly the same in the
mirror world — volume measurements, forces, tracking, speed, ... — so this bug
has gone mostly unnoticed, or noticed and shrugged off and unfixed for all this
time. But it's important for some things!  Your heart is on the left side of
your body, but the right side of your mirror image's. This can be critical, for
example, when using software to plan surgery! Thankfully, we are not aware of
any cases of napari being used in this way. 😅

napari uses zyx coordinates instead of xyz because it is the most natural way
to work with NumPy arrays and the rest of the scientific Python imaging
ecosystem. Flipping the axes in this way also changes the *handedness* of the
space, *unless* you also flip the direction of one of the dimensions. The
simplest way to illustrate this is [this 3D model of a right
shoe](https://grabcad.com/library/anatomic-shoe-sole-euro-right-41-1), which looks
like this in previous versions of napari:

![right shoe rendered as a left shoe in napari](https://github.com/user-attachments/assets/c9190e2c-f35a-44d1-95d5-f9877dd4c843)

and in 0.5.6+, thanks to [#7488](https://github.com/napari/napari/pull/7488):

![right shoe correctly rendered as a right shoe in napari](https://github.com/user-attachments/assets/e187f5e7-8e4a-4526-bae9-80a9bec6fea3)

Most users won't notice. But if you were among the users that noticed and you
implemented workarounds in your code (such as setting the z-scale to a negative
number), now is a good time to undo the workarounds for newer versions of
napari! If you run into any issues please get in touch [on GitHub
issues](https://github.com/napari/napari) or on our [Zulip chat room](https://napari.zulipchat.com)!

### Polygons with holes

Finally, napari is now able to display polygons with holes in them, which starts to open it up for use with mapping data, among other things. Implement polygon with holes in compiled triangulation (#7566)

### Addition of a command palette

The command palette is a new feature that allows you to search for and execute commands in napari. This is a powerful feature that allows you to quickly access and execute commands without having to navigate through the menus. Implement command palette widget (#5483)

### Transition to npe2 plugin engine

npe1 plugins will be automatically converted to npe2 by default (this may break some features if they rely on import-time behaviour).
npe1 plugins will now be automatically converted to npe2 by default (with a warning), which should not change much but it will break plugins that rely on being imported at launch to modify viewer behaviour. You will be able to turn off this automatic conversion in the settings, but this will go away in 0.7.0 (planned for July),
so this is your opportunity to work with plugin authors to migrate to npe2.

## Improved modules and features

### Napari core improvements 🧠

- Implement polygon with holes in compiled triangulation (#7566)
- Add Grid Mode Spacing to change distance between layers (#7597)
- Add API to Camera model to flip axes (#7663)
- Flip z axis on 3D camera to default to right-handed frame (#7488 redux) (#7554)

### GUI improvements 🎨

- Implement command palette widget (#5483)
- Show layer status for all visible layers (#7673)
- Enable creation of custom linear colormaps in layer controls (#7600)
- Change ndisplay button to toggle-like to increase discoverability (#7608)
- Expose additional Camera parameters in GUI with 3D popup widget (#7626)
- Add right-click indicator to 3D, Roll, Grid, and Square push buttons (#7556)
- Fix issues displaying polygons with holes in Shapes (#6654)

### Plugins 

Turn on npe2 adaptor by default and add warning (#7627)

npe1 plugins will be automatically converted to npe2 by default (this may break some features if they rely on import-time behaviour).
npe1 plugins will now be automatically converted to npe2 by default (with a warning), which should not change much but it will break plugins that rely on being imported at launch to modify viewer behaviour.
You will be able to turn off this automatic conversion in the settings,
but this will go away in 0.7.0 (planned for July),
so this is your opportunity to work with plugin authors to migrate to npe2.

### Performance and maintainability

- Pydantic 2.0+ will be required. Remove pydantic v1 compatibility layer, depend on pydantic>=2.2 (#7589) We are requiring Pydantic version 2 and higher. Supporting Pydantic 1 and 2 together was a lot of effort, but by now most plugins and libraries using Pydantic are at version 2, which does bring significant speed and functionality advantages. If you know a library or plugin you use with napari and that is still strictly on Pydantic 1.x, please let us know!
- Python 3.10+ will be required. Update configuration to drop python 3.9 and add python 3.13 (#7603). We are dropping Python 3.9 support. This is slightly earlier than Python 3.9's EOL date (October 2025), but we are still supporting Python 3.10 which is past its recommended window from SPEC0. The bundle follows SPEC0 strictly and so uses Python 3.11. We hope that serves most if not all of our user community!

### Deprecated

- Pending removal in 0.7.0

### Removed

- Removed deprecated items

## Migrating to napari 0.6.0

For napari 0.6.0a1, we recommend installing the preview release:

```bash
pip install napari[all] >= 0.6.0a1
```

*We recommend you update your plugins to npe2. If you have any issues, please let us know!*
