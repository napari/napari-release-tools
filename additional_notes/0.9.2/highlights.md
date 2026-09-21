### Vispy update

In [#9499](https://github.com/napari/napari/pull/9499) we improved and updated [Vispy](https://vispy.org/) (napari's rendering engine), which brings us a few fixes and new features. Some important ones:

- perspective rendering of points and text is no longer broken (Shift+right-click-drag to change FOV in 3D!)
- RGB data can now be viewed in 3D. This might still have some kinks to smooth out, so if you see issues, make sure to report them on the issue tracker.

### Change of type-checker

In [#9395](https://github.com/napari/napari/pull/9395) we decided to change from [`mypy`](https://mypy-lang.org/) to [`pyrefly`](https://pyrefly.org/).
`pyrefly` is faster and support more typing features than `mypy`.

*add blogpost link here*

### More strict release cadence

Based on our experience and feedback from the community, we decided to make our release cadence more strict. We decided to go to monthly cadence with exception for December. The formalization is added in [napari/docs#1126](https://github.com/napari/docs/pull/1126). The actual policy is [here](https://napari.org/stable/developers/coredev/release_policy.html).
