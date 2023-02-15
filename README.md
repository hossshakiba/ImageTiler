# ImageTiler
This project aims to develop an image tiling system that can divide high-resolution images into 𝑚 × 𝑛 tiles while preserving their annotations, including polygons and bounding boxes. Image tiling is an important technique for object detection and segmentation in computer vision. By dividing large images into smaller tiles, this technique can improve the accuracy and efficiency of object detection, particularly for detecting small objects in high-resolution images.

The system will be designed to support different input image formats and annotation types. The user can specify the size of the tiles and the overlap between them. The system will then automatically generate the tiled images and preserve the original annotations in each tile. The annotations will be adjusted to account for the relative position of the tile within the original image.

The system will be particularly useful for segmentation algorithms that require fixed picture sizes. By preserving the annotations in each tile, the system will help to maintain the accuracy of the segmentation. Moreover, the system will allow users to preserve important details in high-resolution images that might be lost when using other image processing techniques.

# Features
* Three different tiling methods: default, overlapping, and padding
* Support for annotations such as polygons and bounding boxes
* Support building tiles from image paths, bytes, and files on MinIO Object Storage


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
Here is a sample code of using ImageTiler:
> Note: Annotations must be in COCO format
```python
# read image annotations (polygons or bounding boxes)
with open('annotations.json', 'r') as file:
    polygons = json.loads(file.read())

# create ImageTilingFactory object with desired tiling parameters
obj = ImageTilingFactory(
    polygons=polygons,
    tile_width=650,
    tile_height=650,
    tiling_type="overlapping"
)

# build the tiles
obj.build_tiles_from_file('images/pandas.jpg')

# draw new annotations on tiles and save them
for image, annotation in zip(obj.tiled_image_files, obj.tiled_annotations):
    image_file, image_file_name = image[0], image[1]
    visualize_keypoints(image_file, annotation, f'overlapping_tiles/{image_file_name}')
```

## Results
The results of the project are organized into different folders, each containing the results of a specific tiling method:
* default
* overlapping
* padding

The following annotated image is divided into tiles with different methods:
<p class="row" float="left" align="middle">
  <img style="width: 100%; height: auto;" src="/images/pandas.png" title="confusion matrix"/>
</p>
Here are four samples of generated 650 × 650 tiles with overlapping method:<br><br>
<p class="row" align="middle">
  <img src="/overlapping_tiles/tiled_pandas_0_350---650_1000.jpg" width="200" height="200" /> 
  <img src="/overlapping_tiles/tiled_pandas_650_0---1300_650.jpg" width="200" height="200" />
  <img src="/overlapping_tiles/tiled_pandas_850_0---1500_650.jpg" width="200" height="200" />
  <img src="/overlapping_tiles/tiled_pandas_850_350---1500_1000.jpg" width="200" height="200"/>
</p>

# Conclusion
The results of the ImageTiler project show that the tool is effective at preserving annotations in the resulting tiles, even for small objects in high-resolution images. The evaluation results demonstrate that the tool can support object detection in high-resolution images. Though trying different methods and tiling sizes based on your images is always suggested to get the best result.

# Future Work
- Sometimes there are some issues with generating new annotations, especially when the original ones are overlapped. These exceptions are ignored now and do not intercept the tiling process. They should get handled in a better way.
- New tiling methods can be added to the project.
# Contributing
If you are interested in contributing to the project, please follow these steps:
1. Fork the repository
2. Create a new branch for your changes
3. Commit your changes and open a pull request

# License
This project is licensed under the MIT license.

# Acknowledgments
- The Shapely package had a crucial role in implementing this project.
- Thank you in advance to all contributors for their time and effort in improving this project. Thank you! :heart:
