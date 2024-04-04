"""
This module contains four napari widgets declared in
different ways:

- a pure Python function flagged with `autogenerate: true`
    in the plugin manifest. Type annotations are used by
    magicgui to generate widgets for each parameter. Best
    suited for simple processing tasks - usually taking
    in and/or returning a layer.
- a `magic_factory` decorated function. The `magic_factory`
    decorator allows us to customize aspects of the resulting
    GUI, including the widgets associated with each parameter.
    Best used when you have a very simple processing task,
    but want some control over the autogenerated widgets. If you
    find yourself needing to define lots of nested functions to achieve
    your functionality, maybe look at the `Container` widget!
- a `magicgui.widgets.Container` subclass. This provides lots
    of flexibility and customization options while still supporting
    `magicgui` widgets and convenience methods for creating widgets
    from type annotations. If you want to customize your widgets and
    connect callbacks, this is the best widget option for you.
- a `QWidget` subclass. This provides maximal flexibility but requires
    full specification of widget layouts, callbacks, events, etc.

References:
- Widget specification: https://napari.org/stable/plugins/guides.html?#widgets
- magicgui docs: https://pyapp-kit.github.io/magicgui/

Replace code below according to your needs.
"""

import shutil
from typing import TYPE_CHECKING

import napari
from magicgui import magic_factory
from magicgui.widgets import (
    CheckBox,
    Container,
    FileEdit,
    FunctionGui,
    PushButton,
    RadioButtons,
    create_widget,
)
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget
from skimage.util import img_as_float

if TYPE_CHECKING:
    import napari


import os

import numpy as np
import pandas as pd
from napari.utils.colormaps import DirectLabelColormap


# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
def threshold_autogenerate_widget(
    img: "napari.types.ImageData",
    threshold: "float",
) -> "napari.types.LabelsData":
    return img_as_float(img) > threshold


# the magic_factory decorator lets us customize aspects of our widget
# we specify a widget type for the threshold parameter
# and use auto_call=True so the function is called whenever
# the value of a parameter changes
@magic_factory(
    threshold={"widget_type": "FloatSlider", "max": 1}, auto_call=True
)
def threshold_magic_widget(
    img_layer: "napari.layers.Image", threshold: "float"
) -> "napari.types.LabelsData":
    return img_as_float(img_layer.data) > threshold


# if we want even more control over our widget, we can use
# magicgui `Container`
class ImageThreshold(Container):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self._viewer = viewer
        # use create_widget to generate widgets from type annotations
        self._image_layer_combo = create_widget(
            label="Image", annotation="napari.layers.Image"
        )
        self._threshold_slider = create_widget(
            label="Threshold", annotation=float, widget_type="FloatSlider"
        )
        self._threshold_slider.min = 0
        self._threshold_slider.max = 1
        # use magicgui widgets directly
        self._invert_checkbox = CheckBox(text="Keep pixels below threshold")

        # connect your own callbacks
        self._threshold_slider.changed.connect(self._threshold_im)
        self._invert_checkbox.changed.connect(self._threshold_im)

        # append into/extend the container with your widgets
        self.extend(
            [
                self._image_layer_combo,
                self._threshold_slider,
                self._invert_checkbox,
            ]
        )

    def _threshold_im(self):
        image_layer = self._image_layer_combo.value
        if image_layer is None:
            return

        image = img_as_float(image_layer.data)
        name = image_layer.name + "_thresholded"
        threshold = self._threshold_slider.value
        if self._invert_checkbox.value:
            thresholded = image < threshold
        else:
            thresholded = image > threshold
        if name in self._viewer.layers:
            self._viewer.layers[name].data = thresholded
        else:
            self._viewer.add_labels(thresholded, name=name)


class ExampleQWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer

        btn = QPushButton("Click me!")
        btn.clicked.connect(self._on_click)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(btn)

    def _on_click(self):
        print("napari has", len(self.viewer.layers), "layers")


def set_label_colormap_function(table: pd.DataFrame):
    pass


class set_label_colormap(FunctionGui):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(
            set_label_colormap_function, call_button=False, persist=True
        )
        self.viewer = viewer
        self.colormap_file = FileEdit(label="Get colormap from file")
        self.insert(-1, self.colormap_file)
        self.label_names = RadioButtons(label="Label names", choices=[])
        self.file_button = PushButton(label="Load colormap")
        self.file_button.clicked.connect(self.update_colormap)
        self.insert(-1, self.file_button)
        self.insert(-1, self.label_names)

        # self.colormap_file.changed.connect(self.update_colormap)
        self.label_names.changed.connect(self.update_selected_label)
        # Check if /tmp/last_cmap_napari.txt exists
        if os.path.exists("/tmp/last_cmap_napari.txt"):
            try:
                self.colormap_file.value = "/tmp/last_cmap_napari.txt"
                # Click the file_button
                self.file_button.clicked()
            except:
                napari.utils.notifications.show_info(
                    "Error: Could not load last colormap"
                )

    def get_colormap(self, file):
        cmap = DirectLabelColormap()
        with open(file) as f:
            labels = f.read().splitlines()
        # Keep only values after the second occurence of "################################################"
        labels = labels[
            labels.index("################################################")
            + 1 :
        ]
        labels = labels[
            labels.index("################################################")
            + 1 :
        ][1:]
        choices = {"choices": ["0"], "key": ["0 - Background"]}
        colormap = {}
        # colormap_hex = {0: "#000000"}
        colormap = {0: np.array([0, 0, 0, 0]).astype("float32")}
        for label in labels:
            label = label.split()
            val = label[0]
            color = np.array(label[1:4]).astype("float32") / 255.0
            name = " ".join(label[7:]).replace('"', "")
            choices["key"].append(str(val) + " - " + name)
            choices["choices"].append(str(val))
            colormap[int(val)] = np.concatenate(
                [color, np.array([0.5], dtype="float32")]
            )

        cmap.color_dict.update(colormap)
        key = choices["key"]
        # Convert key as a callable function that takes choices['choices'] as input and returns key
        choices["key"] = lambda x: key[choices["choices"].index(x)]
        self.cmap = cmap
        self.choices = choices
        # Save cmap

    def update_colormap(self):
        if self.colormap_file.value != "":
            self.get_colormap(self.colormap_file.value)
            self.apply_cmap()
            # Copy file self.colormap_file.value (filename) to /tmp/last_cmap_napari.txt
            try:
                shutil.copy(
                    self.colormap_file.value, "/tmp/last_cmap_napari.txt"
                )
            except shutil.SameFileError:
                pass

            # print(DirectLabelColormap(list(colormap.values())))
            # Get napari.layers.Labels from self.labels_layer
            # label_layer=[os.path.basename(x.name) for x in self.viewer.layers if isinstance(x,napari.layers.Labels)] #and x.name==self.labels_layer.value][0]
            # print(label_layer.colormap.color_dict)

    def apply_cmap(self):
        for layer in [
            x
            for x in self.viewer.layers
            if isinstance(x, napari.layers.Labels)
        ]:
            layer.colormap = self.cmap

        self.label_names.choices = self.choices

    def update_selected_label(self):
        for layer in [
            x
            for x in self.viewer.layers
            if isinstance(x, napari.layers.Labels)
        ]:
            layer.selected_label = int(self.label_names.value)


def process_multi_channel_function(img: "napari.layers.Image"):
    pass


class process_multi_channel(FunctionGui):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(
            process_multi_channel_function, call_button=False, persist=True
        )
        self.viewer = viewer
        self.operation = RadioButtons(
            label="Operation", choices=["concatenate", "split", "average"]
        )
        self.insert(-2, self.operation)
        self.dim = 0
        # self.insert(-1,self.dim)
        # #If img is not None, update dim
        # self.img.changed.connect(self.auto_update_dim)
        # if self.img.value is not None:
        #     self.auto_update_dim()

        self.push_button = PushButton(label="Process")
        self.insert(-1, self.push_button)
        self.push_button.clicked.connect(self.update_operation)

    def auto_update_dim(self):
        shape = self.img.value.data.shape
        # Get the smallest dimension
        self.dim.value = shape.index(min(shape))

    def update_operation(self):
        if self.operation.value == "concatenate":
            # Stack the images along the dimension dim
            # Get the image from self.img
            new_layer = self.img.value.data
            # new_layer=np.moveaxis(new_layer,self.dim.value,0)
            new_layer = np.concatenate(
                [new_layer[i] for i in range(new_layer.shape[0])]
            )
            # Get the self.image layer
            spacing = self.img.value.metadata["spacing"][:3]
            scale = list(spacing)[
                ::-1
            ]  # Remove the dimension dim from the scale
            affine = np.eye(4)
            affine[0, 0] = spacing[2]
            affine[1, 1] = spacing[1]
            affine[2, 2] = spacing[0]
            scale = np.array([1.0, 1.0, 1.0])
            # #Remove column and row dim from the affine
            # affine=np.delete(affine,self.dim.value,0)
            # affine=np.delete(affine,self.dim.value,1)
            metadata = self.img.value.metadata
            print(metadata)
            dir=metadata['direction']
            new_direction=(dir[0],dir[1],dir[2],dir[4],dir[5],dir[6],dir[8],dir[9],dir[10])
            new_metadata={'dim[4]':'1',"pixdim[4]":'1','origin':metadata['origin'][0:3],'spacing':metadata['spacing'][0:3],'direction':new_direction}
            
            self.viewer.add_image(
                new_layer,
                name=f"{self.img.name}_concatenated",
                scale=scale,
                affine=affine,
                metadata=metadata.update(new_metadata)
            )

    #     self.update_operation()

    # def update_operation(self):
    #     if self.operation.value=='stack':
    #         self.viewer.layers.selection.active='stack'
    #     else:
    #         self.viewer.layers.selection.active='average'
    #     self.viewer.layers.selection.active=self.operation.value
