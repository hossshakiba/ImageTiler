# ImageTiler
A project for dividing images into 𝑚 × 𝑛 tiles while keeping their annotations
(polygons, Bounding boxes) in the correct form. Image tiling is typically used
for detecting small objects in high-resolution images. Some segmentation algorithms only accept
fixed picture sizes. In these cases, we resize the picture by default which might end up in a loss of details. 
Tiling images helps preserve the details but breaks down your image into smaller tiles. 
This option works best when your objects' micro and macro visual features are very similar, i.e., Cracks, Corrosion, etc. 
But it only works well with objects that require visual continuity, like humans.<br>

# Features
* Three different tiling methods: default, overlapping, and padding
* Support for annotations such as polygons and bounding boxes
* Support building tiles from image paths, bytes, and MinIO Object Storage

> Note: Annotations must be in COCO format

# Getting Started

## Installing

1. Clone the repository
```bash
git clone https://github.com/hossshakiba/ImageTiler.git
```
2. Install dependencies
```bash
pip install -r requirements.txt
```

## Usage
Here is how you can divide an image into tiles
```python
    polygons = [
        {'segmentation': [[13, 885, 987, 12, 947, 12, 13, 855]]},
        {'segmentation': [[1102, 12, 13, 1423, 13, 976]]},
        {'segmentation': [[241, 1345, 174, 1589, 13, 1589]]},
        {'segmentation': [[2488, 12, 2285, 253, 2335, 12]]},
        {'segmentation': [[2488, 155, 1478, 1589, 2488, 545]]},
        {'segmentation': [[2488, 690, 1636, 1589, 1683, 1589, 2488, 717]]},
        {'segmentation': [[2488, 929, 2003, 1589, 2488, 1584]]}
    ]

    obj = ImageTilingFactory(
        polygons=polygons,
        tile_width=400,
        tile_height=500,
        tiling_type="overlapping"
    )
    
    obj.build_tiles_from_file('IMAGE_PATH').save_to_file('FOLDER_PATH')
```
