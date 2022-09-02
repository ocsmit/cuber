from dataclasses import dataclass

from typing import Optional, Union
from pathlib import Path
import json
from rasterio.features import bounds


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
    crs: Optional[str] = "EPSG:4326"

    def __post_init__(self):
        """ """

        self.upper_left = [self.top, self.left]
        self.lower_right = [self.bottom, self.right]


def create_Bbox(geojson_path: Path, crs: str = "EPSG:4326") -> Bbox:
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

    return Bbox(*bounds(geom), crs=crs)
