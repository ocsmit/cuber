from pathlib import Path
import json
from dataclasses import dataclass
from typing import List, Tuple, Union

import numpy as np

import rasterio as rio
from rasterio.features import bounds
from rasterio.warp import reproject, calculate_default_transform, Affine

# from pyproj import Transformer


@dataclass
class Bbox:
    """Struct for bounding box

    Parameters
    ----------
    left : Union[int, float]
        Left most coordinate

    bottom : Union[int, float]
        Bottom most coordinate

    right : Union[int, float]
        Right most coordinate

    top : Union[int, float]
        Top most coordinate

    Attributes
    ----------
    left : Union[int, float]

    bottom : Union[int, float]

    right : Union[int, float]

    top : Union[int, float]

    upper_left: List[int, float]

    lower_right: List[int, float]

    Notes
    -----
    The bounding box can be thought as
    .. math:: B = \{\min(y), \min(x), \max(y), \max(x)\}


    What is best method to enforce bounding box topological rules?
    Assume the CRS is WGS 84 and the first instinct is a bounding box
    B is only valid if R > L and T > B. For most cases this holds,
    However on the edge case is where a bounding box goes from
    right and loops back to the left, or loops from bottom to top.

    Example
    -------
    """

    left: Union[int, float]
    bottom: Union[int, float]
    right: Union[int, float]
    top: Union[int, float]

    def __post_init__(self):
        """ """

        self.upper_left = [self.top, self.left]
        self.lower_right = [self.bottom, self.right]


@dataclass
class TransformParams:
    """TransformParams

    Parameters
    ----------
    transform : Affine
        Affine class

    width: Union[int, None]
        Width of new ndarray

    height: Union[int, None]
        Height of new ndarray

    crs: str
        CRS of new ndarray

    bands: List[int]
        Number of bands in rasterio object.
        Will be additional dimension of new ndarray

    Attributes
    ----------
    transform : Affine

    width: Union[int, None]

    height: Union[int, None]

    crs: str

    bands: List[int]


    Notes
    -----



    Example
    -------
    """

    transform: Affine
    width: Union[int, None]
    height: Union[int, None]
    crs: str
    bands: List[int]

    def __to_rowcol(self, lat, lng) -> Tuple[int, int]:
        """private method to get row and col of array from spatial coordinate

        Parameters
        ----------
        lat : Union[int, float]
            Latitude of point

        lng : Union[int, float]
            Longitude of point

        Returns
        -------
        Tuple[int, int]
            Tuple of [i, j] (row, col)

        Notes
        -----
        (Latitude, Longitude) ~ (Y, X)

        Example
        -------
        """

        gt = self.transform
        ulX = gt[2]
        ulY = gt[5]
        xDist = gt[0]
        yDist = gt[4]
        pixel = abs(int((lng - ulX) / xDist))
        line = abs(int((ulY - lat) / yDist))
        return (line, pixel)

    def slice(self, ul, lr) -> List[Tuple[int, int]]:
        """slice

        Parameters
        ----------
        ul : List[Union[int, float]]
            Upper left coordinate of bounding box

        lr : List[Union[int, float]]
            Lower right coordinate of bounding box

        Returns
        -------
        List[Tuple[int, int]]
            The rows and cols to slice an array based on spatial bounding box

        Notes
        -----
        Array can be sliced with output like
        >>> arr[:, arr_slice[0][0] : arr_slice[1][0], arr_slice[0][1] : arr_slice[1][1]]

        Example
        -------
        """
        return list(map(lambda x: self.__to_rowcol(*x), [ul, lr]))


def create_Bbox(geojson_path: Path) -> Bbox:
    """create Bbox struct from geojson on disk

    Parameters
    ----------
    geojson_path : Path
        Path to geojson file


    Returns
    -------
    Bbox
        Bbox struct

    Notes
    -----
       Will change to be more robust

    Example
    -------
    """
    with open(str(geojson_path.resolve())) as fp:
        geojson = json.load(fp)

    geom = geojson["features"][0]["geometry"]
    assert geom != None

    return Bbox(*bounds(geom))


def create_TransformParams(
    src: rio.DatasetReader, output_crs: str = "EPSG:4326"
) -> TransformParams:
    """create_TransformParams

    Parameters
    ----------
    src : rio.DatasetReader
        Open rasterio data

    output_crs : str, default: "EPSG:4326"
        Acceptable CRS string

    Returns
    -------
    TransformParams
        Struct holding neccesary geotransform information
        to align to new raster grid

    Notes
    -----

    Example
    -------
    >>> create_TransformParams(rio.open("./geo.tif", "EPSG:4326")
    """
    # NOTE: Add type checking
    return TransformParams(
        *calculate_default_transform(
            src.crs,
            output_crs,
            src.width,
            src.height,
            *src.bounds,
        ),
        output_crs,
        list(range(1, src.count + 1)),
    )


def align_src(src, transform_params: TransformParams) -> np.ndarray:
    """Align a raster based on specification of transform

    Parameters
    ----------
    src : rasterio.DatasetReader
        Opened rasterio object

    transform_params : TransformParams
        TransormParams object containing desired spatial information to align

    Returns
    -------
    np.ndarray
        N-dimensional array aligned to new geotransform

    Notes
    -----

    Example
    -------
    """

    assert (
        all((transform_params.height, transform_params.width)) != None
    ), "Invalid width or height"

    # NOTE: Figure out how to force int typing
    dst_data = np.empty(
        (
            len(transform_params.bands),
            transform_params.height,
            transform_params.width,
        )
    )
    # Align to new grid
    reproject(
        source=rio.band(src, transform_params.bands),
        destination=dst_data,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform_params.transform,
        dst_crs=transform_params.crs,
    )
    return dst_data


def cube(srcs, crs, bbox) -> List[np.ndarray]:
    """cube vector of rasterio objects

    Parameters
    ----------
    srcs : List[rasterio.DatasetReader]
        list of opened rasterio objects

    crs : str
        Desired CRS

    bbox : Bbox
        Bbox in which to clip data

    Returns
    -------
    List[np.ndarray]
        List of cubed ndarrays aligned and clipped to grid

    Notes
    -----

    Example
    -------
    """
    trans = create_TransformParams(srcs[0], crs)
    arr_slice = trans.slice(bbox.upper_left, bbox.lower_right)
    outputs = []
    for i in srcs:
        out = align_src(i, trans)[
            :, arr_slice[0][0] : arr_slice[1][0], arr_slice[0][1] : arr_slice[1][1]
        ]
        outputs.append(out)

    return outputs
