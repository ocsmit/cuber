import pytest
import json


@pytest.fixture
def bbox_json():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-78.69146347045898, 35.75584628737584],
                            [-78.65129470825195, 35.75584628737584],
                            [-78.65129470825195, 35.794703076697026],
                            [-78.69146347045898, 35.794703076697026],
                            [-78.69146347045898, 35.75584628737584],
                        ]
                    ],
                },
            }
        ],
    }
