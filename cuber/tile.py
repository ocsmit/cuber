"""
                ┌─────────────┐
                │base geo, CRS│
                └──────┬──────┘
                       │
                       ▼
           ┌────────────────────────┐   ┌─────────────────┐
           │ TransformerParams      │   │ Bbox            │
           │   - transform : Affine │   │   - left        │
           │   - width : int        │   │   - right       │
           │   - height : int       │   │   - top         │
           │   - crs : str          │   │   - crs         │
           │   - bands : List[int]  │   │   - upper_left  │
           └───────────┬────────────┘   │   - lower_right │
                       │                └────────┬────────┘
                       │                         │
                       │                         │
                       └──────────┬──────────────┘
                                  │
                                  ▼
            ┌──────────────────────────────────────────────┐
            │ Slice                                        │
            │   - height = abs(i_1 - i_2)                  │
            │   - width = abs(j_1 - j_2)                   │
            │                                              │
            │   i_n, j_n refer to the min, and max i,j     │
            │   determined from converting the Bbox to     │
            │   row col indicies with the new geotransform │
            └─────────────────────┬────────────────────────┘
                                  │
                                  ▼
            ┌─────────────────────────────────────────────┐
            │ tiledb                                      │
            │   - empty_like(<uri>, arr_shape, *, ...)    │
            │                                             │
            │   We can generate the tiledb on disk before │
            │   any numpy computation since we know the   │
            │   size of our output array at runtime.      │
            └─────────────────────────────────────────────┘

"""


from pathlib import Path
from numpy import datetime64
import tiledb
from dataclasses import dataclass
from typing import List, Tuple, Union
from bbox import BBox
from transform import TransformParams


@dataclass
class TileCube:
    uri: Union[str, Path]
    attr: str
    width: int
    height: int
    bands: List[int]
    dates: List[datetime64]
    crs: str
    bbox: BBox

    @property
    def shape(self) -> Tuple[int, int, int, int]:
        return (
            len(self.bands),
            self.height,
            self.width,
            len(self.dates),
        )

    def create(self, *, overwrite=False) -> None:
        tiledb.empty_like(str(self.uri), self.shape)
        with tiledb.open(str(self.uri), "w") as ARR:
            ARR.meta["crs"] = self.crs
            ARR.meta["upper_left"] = self.bbox.upper_left
            ARR.meta["lower_right"] = self.bbox.lower_right
            ARR.meta["dates"] = self.dates


def create_TileCube(
    uri: Union[str, Path],
    attr: str,
    bands: List[int],
    dates: List[datetime64],
    bbox: BBox,
    transparams: TransformParams,
    *,
    create=False,
    overwrite=False,
) -> TileCube:
    """Method to create TileCube object

    Parameters
    ----------
    uri : Union[str, Path]
       Path to tiledb instance

    attr : str
        Attribute value within tiledb instance

    width : int

    height : int

    bbox : BBox
        Spatial information to include in metadata



    """
    if isinstance(uri, str):
        uri = Path(uri)
    assert uri.exists(), f"Path ({uri.__str__}) to TileDB does not exist"

    arr_slice = transparams.slice(bbox.upper_left, bbox.lower_right)
    height = abs(arr_slice[0][0] - arr_slice[1][0])
    width = abs(arr_slice[0][1] - arr_slice[1][1])

    tilecube = TileCube(
        uri=uri,
        attr=attr,
        width=width,
        height=height,
        bands=bands,
        dates=dates,
        crs=transparams.crs,
        bbox=bbox,
    )
    if create:
        tilecube.create(overwrite=overwrite)

    return tilecube
