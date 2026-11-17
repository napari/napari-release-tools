This is a maintenance-focused release: it has few new features, but contains a ton of performance and maintenance work that will enhance both working _with_ napari and _on_ napari! And of course, tons of bug fixes :)

### CI speedups and improvements

Our automated testing and deploying machinery (CI) has accumulated slowness and technical debt over the years. During this release cycle, we tackled several of these issues (chief among them ([#9870](https://github.com/napari/napari/pull/9870))) and cut test time on our pull request by up to half!

### Various Performance enhancements

`Labels` painting, `Shapes` and slicing in general got several performance improvements. Many workflows will benefit from this, so make sure to try out things that used to be slow to check if you're one of the lucky winners ;)

### Typing progress

The napari codebase is getting more and move type annotation coverage! This release merged more than a dozen typing-related pull request, which helped (and will help) us find bugs and develop both napari and napari plugins more easily. We'll continue this trend in the upcoming releases!
