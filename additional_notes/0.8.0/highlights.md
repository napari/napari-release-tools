The napari 0.8.0 is released that drops support for python 3.10 [#9104](https://github.com/napari/napari/pull/9104) and deprecate support for pyqt5 [#9079](https://github.com/napari/napari/pull/9079). But we also ship some new fetures and improvements. Here are some of the highlights:

### Drop of support for python 3.10 and pyqt5

To improve the maintainability of napari, we have dropped support for python 3.10 and deprecated support for pyqt5. Python 3.10 will reach end of life in October 2026, but many packages have already dropped support for it, and keep maintaining support for it is becoming increasingly difficult. 

PyQt5 is already reached its end of life. We already dropped support for PySide2 in napari 0.7.0. As PyQt5 is quite stable we decided to deprecate it in 0.8.0 and will drop support for it on fall 2026. If your project is still depending on qt5, please consider migrating to PySide6 or PyQt6.

### Histogram for Image layer

In [#8391](https://github.com/napari/napari/pull/8391) we added a histogram view for the Image layer, So you could easily see brightness distribution of the image. The histogram is shown in the layer controls when the Image layer is selected. Histogram is rendered based on visible data.

### Fixing the drawing circle and square shapes

In the [#9018](https://github.com/napari/napari/pull/9018) we fixed the drawing of circle and square using the Shift modifier key. Now the shape follow the mouse, not just grow to bottom right. 

### Floating axes overlays 

Thanks to [#8262](https://github.com/napari/napari/pull/8262) the axes overlay could be always visible, floating over the data instead of being fixed to the top right corner of data. Find them in View menu. 

### Improving the napari Theme 

In [#9078](https://github.com/napari/napari/pull/9078) and [#8927](https://github.com/napari/napari/pull/8927) we unify colors across the application elements and adjust some colors to improve the overall visual consistency. 



