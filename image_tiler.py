import copy
import os
import io
from itertools import product

import cv2
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.validation import make_valid


def visualize_keypoints(image, keypoints, path, color=(0, 255, 0), diameter=10):
    image = np.asarray(image)
    for keypoint in keypoints:
        polygons = []
        while len(keypoint['segmentation'][0]) > 0:
            x, y = keypoint['segmentation'][0].pop(0), keypoint['segmentation'][0].pop(0)
            polygons.append([x, y])
            cv2.circle(image, (int(x), int(y)), diameter, (0, 255, 0), -1)

        pts = np.array(polygons, np.int32)
        image = cv2.polylines(image, [pts], True, color, 4)

    cv2.imwrite(path, image)


class ImageTilingFactory:
    TILING_TYPE_DEFAULT = "default"
    TILING_TYPE_OVERLAPPING = "overlapping"
    TILING_TYPE_PADDING = "padding"

    def __init__(self, polygons: list, tile_width, tile_height, tiling_type: str = TILING_TYPE_DEFAULT):
        self.tiled_image_files = []
        self.image_path = None
        self.image_name = None
        self.polygons = polygons
        self.tiling_type = tiling_type
        self.tiled_annotations = []
        self.tiled_images = []
        self.image = None
        self.tile_width = tile_width
        self.tile_height = tile_height

    @property
    def cartesian_product(self):
        if self.tiling_type == self.TILING_TYPE_DEFAULT:
            return self.default_cartesian_product()
        elif self.tiling_type == self.TILING_TYPE_OVERLAPPING:
            return self.overlapping_cartesian_product()
        elif self.tiling_type == self.TILING_TYPE_PADDING:
            return self.padding_cartesian_product()
        raise NameError(f"{self.tiling_type} is not an acceptable tiling_type.")

    @property
    def category_polygon(self):
        category_polygon_tuples = []
        for item in self.polygons:
            if item['segmentation']:
                x_coordinates = item['segmentation'][0][0::2]
                y_coordinates = item['segmentation'][0][1::2]
                category_polygon_tuples.append(
                    (item['category_id'], list(map(lambda x, y: (x, y), x_coordinates, y_coordinates)))
                )
            elif not item['segmentation'] and item['bbox']:
                x_min, y_min = item['bbox'][0], item['bbox'][1]
                x_max, y_max = x_min + item['bbox'][2], y_min + item['bbox'][3]
                category_polygon_tuples.append((
                    item['category_id'],
                    [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max), (x_min, y_min)]
                ))
        return category_polygon_tuples

    def default_cartesian_product(self):
        return product(
            range(0, self.image.width - self.image.width % self.tile_width, self.tile_width),
            range(0, self.image.height - self.image.height % self.tile_height, self.tile_height)
        )

    def overlapping_cartesian_product(self):
        list1 = list(range(0, self.image.width - self.image.width % self.tile_width, self.tile_width))
        list2 = list(range(0, self.image.height - self.image.height % self.tile_height, self.tile_height))
        if self.image.width % self.tile_width > 0:
            list1 += [self.image.width - self.tile_width]
        if self.image.height % self.tile_height > 0:
            list2 += [self.image.height - self.tile_height]
        return product(
            list1, list2
        )

    def padding_cartesian_product(self):
        return product(
            range(0, self.image.width, self.tile_width),
            range(0, self.image.height, self.tile_height)
        )

    @staticmethod
    def segmentation_to_x_y(segmentation):
        x_coordinates = segmentation[0::2]
        y_coordinates = segmentation[1::2]
        return x_coordinates, y_coordinates

    def segmentation_health_check(self, segmentation, width, height):
        new_segmentation = []
        x_coordinates, y_coordinates = self.segmentation_to_x_y(segmentation)
        for x, y in zip(x_coordinates, y_coordinates):
            if x >= width:
                x = width - 1
            elif x <= 0:
                x = 1
            if y >= height:
                y = height - 1
            elif y <= 0:
                y = 1
            new_segmentation += [x, y]
        return new_segmentation

    @staticmethod
    def bbox_health_check(bbox, width, height):
        x_min, x_max = bbox[0] / width, (bbox[0] + bbox[2]) / width  # albumentations library format
        y_min, y_max = bbox[1] / height, (bbox[1] + bbox[3]) / height  # albumentations library format
        for value in [x_min, y_min, x_max, y_max]:
            if not 0 < value <= 1:
                return False
        if x_max <= x_min or y_max <= y_min:
            return False
        if any(x <= 0 for x in [x_min, y_min, x_max, y_max]):
            return False
        if bbox[0] >= width:
            return False
        if bbox[1] >= height:
            return False
        return True

    def segmentation_to_bbox(self, segmentation):
        x, y = self.segmentation_to_x_y(segmentation)
        x_min, x_max, y_min, y_max = min(x), max(x), min(y), max(y)
        bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
        return bbox

    def segmentation_area(self, segmentation):
        bbox = self.segmentation_to_bbox(segmentation)
        width = bbox[2]
        height = bbox[3]
        return float(width * height)

    def save_to_folder(self, destination_path, image_file):
        cv2.imwrite(
            os.path.join(destination_path),
            np.asarray(image_file)
        )
        return self

    @staticmethod
    def __get_image_from_local(image_path):
        try:
            return Image.open(image_path)
        except FileNotFoundError as fnf:
            raise fnf
        except Exception as e:
            raise e

    @staticmethod
    def __get_image_from_s3(image_path, client, bucket_name):
        try:
            response = client.get_object(bucket_name, image_path)
            image = io.BytesIO(response.read())
            return Image.open(image)
        except ConnectionError:
            raise ConnectionError("Ooops! There seems to be a connection issue. Please Try again in a while.")
        except Exception as e:
            raise e
        finally:
            response.close()
            response.release_conn()

    def make(self):
        for x_min, y_min in self.cartesian_product:
            box_width = x_min + self.tile_width
            box_height = y_min + self.tile_height
            box = (x_min, y_min, box_width, box_height)
            self.build_tile(self.image.crop(box), x_min, y_min, box_width, box_height)

    def build_tiles_from_file(self, image_path):
        self.image_path = image_path
        self.image_name = os.path.basename(image_path).split(".")[0]
        self.image = self.__get_image_from_local(image_path)
        self.make()
        return self

    def build_tiles_from_s3(self, image_path, client, bucket_name):
        self.image_path = image_path
        self.image_name = os.path.basename(image_path).split(".")[0]
        self.image = self.__get_image_from_s3(image_path, client, bucket_name)
        self.make()
        return self

    def build_tiles_from_bytes(self, image_bytes: bytes, image_name):
        self.image_name = image_name
        self.image = Image.open(io.BytesIO(image_bytes))
        self.make()
        return self

    def build_tile(self, image, start_x, start_y, end_x, end_y):
        new_file_name = f'tiled_{self.image_name}_{start_x}_{start_y}---{end_x}_{end_y}.jpg'
        bbox_polygon = Polygon(
            [[start_x, start_y], [end_x, start_y], [end_x, end_y], [start_x, end_y], [start_x, start_y]]
        )

        new_annotations = []
        for category_id, poly in self.category_polygon:
            try:
                temp_poly = make_valid(Polygon(poly))
                target_polygon = bbox_polygon.intersection(temp_poly)
                result = []
                if target_polygon.is_empty or isinstance(target_polygon, LineString):
                    continue
                if isinstance(target_polygon, Polygon):
                    for x, y in zip(target_polygon.boundary.xy[0], target_polygon.boundary.xy[1]):
                        result.append(x - start_x)
                        result.append(y - start_y)
                elif isinstance(target_polygon, MultiPolygon):
                    for x, y in zip(target_polygon.boundary.xy[0], target_polygon.boundary.xy[1]):
                        result.append(x)
                        result.append(y)
            except Exception as e:
                print(e)
                print('#'*30)
                continue
            if not result:
                continue
            result = self.segmentation_health_check(result, self.tile_width, self.tile_height)
            bbox = self.segmentation_to_bbox(result)
            if not self.bbox_health_check(bbox, self.tile_width, self.tile_height):
                continue

            new_annotations.append({
                "category_id": category_id,
                "segmentation": [result],
                "bbox": bbox,
                "area": self.segmentation_area(result),
                "iscrowd": 0
            })

        self.tiled_images.append({
            "width": self.tile_width,
            "height": self.tile_height,
            "file_name": new_file_name
        })
        self.tiled_annotations.append(copy.deepcopy(new_annotations))
        self.tiled_image_files.append((image, new_file_name))

        return self


if __name__ == '__main__':
    polygons = [
        {'category_id': 12, 'segmentation': [[13, 885, 987, 12, 947, 12, 13, 855]]},
        {'category_id': 12, 'segmentation': [[1102, 12, 13, 1423, 13, 976]]},
        {'category_id': 12, 'segmentation': [[241, 1345, 174, 1589, 13, 1589]]},
        {'category_id': 12, 'segmentation': [[2488, 12, 2285, 253, 2335, 12]]},
        {'category_id': 12, 'segmentation': [[2488, 155, 1478, 1589, 2488, 545]]},
        {'category_id': 12, 'segmentation': [[2488, 690, 1636, 1589, 1683, 1589, 2488, 717]]},
        {'category_id': 12, 'segmentation': [[2488, 929, 2003, 1589, 2488, 1584]]}
    ]

    obj = ImageTilingFactory(
        polygons=polygons,
        tile_width=400,
        tile_height=500,
        tiling_type="overlapping"
    )
    obj.build_tiles_from_file('hoss.jpg').save_to_folder('images')
