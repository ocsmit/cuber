from dataclasses import dataclass
from typing import Union, List, Tuple

import rasterio as rio
from rasterio.warp import Affine, calculate_default_transform


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
    width: int
    height: int
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
    trans = calculate_default_transform(
        src.crs,
        output_crs,
        src.width,
        src.height,
        *src.bounds,
    )
    assert isinstance(trans[2], int) and isinstance(
        trans[1], int
    ), f"Invalid width and height (f{trans[1]}, {trans[2]})"
    return TransformParams(
        trans[0],
        trans[1],
        trans[2],
        output_crs,
        list(range(1, src.count + 1)),
    )
