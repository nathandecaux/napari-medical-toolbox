import numpy as np
from napari.utils.colormaps import DirectLabelColormap
from napari.utils.colormaps import colormap_utils as cu

# Open napari with napari-medical-toolbox
palette = {
    0: np.array((0.0, 0.0, 0.0, 0.0)),
    1: np.array((0.0, 0.0, 0.0, 1.0)),
}
# palette=glasbey.create_palette(16)
colormap = cu.label_colormap()
# print(colormap)

# cmap=DirectLabelColormap(glasbey.create_palette(16))
# cmap.color_dict.update({0:np.array((0.,0.,0.,0.)),1:np.array((0.,0.,0.,1.))})


def get_colormap(file):
    cmap = DirectLabelColormap()
    print(cmap.dict())
    with open(file) as f:
        labels = f.read().splitlines()
    # Keep only values after the second occurence of "################################################"
    labels = labels[
        labels.index("################################################") + 1 :
    ]
    labels = labels[
        labels.index("################################################") + 1 :
    ][1:]
    choices = {"choices": ["0"], "key": ["0 - Background"]}
    colormap = {}
    colormap_hex = {0: "#000000"}
    colormap = {0: np.array([0, 0, 0, 0]).astype("float32")}
    for label in labels:
        label = label.split()
        val = label[0]
        color = np.array(label[1:4]).astype("float32") / 255.0
        name = " ".join(label[7:]).replace('"', "")
        choices["key"].append(str(val) + " - " + name)
        choices["choices"].append(str(val))
        colormap[int(val)] = np.concatenate(
            [color, np.array([1.0], dtype="float32")]
        )

    return cmap.color_dict.update(colormap)


cmap = get_colormap("labels_2.txt")
# DirectLabelColormap(cmap)
