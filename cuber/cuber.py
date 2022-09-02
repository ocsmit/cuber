from pathlib import Path, PosixPath
import json
from dataclasses import dataclass
from typing import Any, List, Tuple, Union

import numpy as np

import rasterio as rio
from rasterio.features import bounds
from rasterio.warp import reproject, calculate_default_transform, Affine

if __package__:
    from .bbox import Bbox, create_Bbox
    from .transform import TransformParams, create_TransformParams
else:
    from bbox import Bbox, create_Bbox
    from transform import TransformParams, create_TransformParams


# from pyproj import Transformer
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


def homogeneous_type(seq: List[Any]) -> Union[type, bool]:
    iseq = iter(seq)
    first_type = type(next(iseq))
    return first_type if all(isinstance(x, first_type) for x in iseq) else False


def cube(src, crs, bbox) -> np.ndarray:
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
    list_type = homogeneous_type(src)
    assert list_type != False, "Provide list of same types"

    if not isinstance(list_type, rio.DatasetReader):
        base_item = rio.open(src[0])
        opened = False
    else:
        base_item = src[0]
        opened = True

    # base_item = rio.open(src[0]) if isinstance(list_type, (str, PosixPath)) else src[0]

    trans = create_TransformParams(base_item, crs)
    arr_slice = trans.slice(bbox.upper_left, bbox.lower_right)
    height = abs(arr_slice[0][0] - arr_slice[1][0])
    weight = abs(arr_slice[0][1] - arr_slice[1][1])
    data_cube = np.zeros((base_item.count, height, weight, len(src)))
    outputs = []
    for idx, i in enumerate(src):
        print(i)
        if not opened:
            i = rio.open(i)
        data_cube[..., idx] = align_src(i, trans)[
            :, arr_slice[0][0] : arr_slice[1][0], arr_slice[0][1] : arr_slice[1][1]
        ]
        # outputs.append(out)

    return data_cube