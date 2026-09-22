### Vispy update

In [#9499](https://github.com/napari/napari/pull/9499) we improved and updated [Vispy](https://vispy.org/) (napari's rendering engine), which brings us a few fixes and new features. Some important ones:

- perspective rendering of points and text is no longer broken (Shift+right-click-drag to change FOV in 3D!)
- RGB data can now be viewed in 3D. This might still have some kinks to smooth out, so if you see issues, make sure to report them on the issue tracker.

### Change of type-checker

In [#9395](https://github.com/napari/napari/pull/9395) we decided to change from [`mypy`](https://mypy-lang.org/) to [`pyrefly`](https://pyrefly.org/).
`pyrefly` is faster and support more typing features than `mypy`.

*add blogpost link here*

### New release policy with regular cadence

The napari team has been working hard to improve our release process, and based on our experience and feedback from the community, we have formally adopted a release policy ([napari/docs#1126](https://github.com/napari/docs/pull/1126)). Expect regular monthly releases and clearer communication about review and timing for contributions; read the [full policy](https://napari.org/stable/developers/coredev/release_policy.html).
