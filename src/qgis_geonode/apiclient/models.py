import dataclasses
import datetime as dt
import enum
import math
import typing
from uuid import UUID

import qgis.core
from qgis.PyQt import (
    QtCore,
    QtXml,
)

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsRectangle,
)

from ..utils import IsoTopicCategory

UNSUPPORTED_REMOTE = "unsupported"


class ApiClientCapability(enum.Enum):
    # NOTE - Some capabilities are not made explicit here because their support
    # is mandatory far all API clients. For example, all clients must support
    # searching datasets, as otherwise there wouldn't be much point to their existence
    FILTER_BY_NAME = enum.auto()
    FILTER_BY_ABSTRACT = enum.auto()
    FILTER_BY_KEYWORD = enum.auto()
    FILTER_BY_TOPIC_CATEGORY = enum.auto()
    FILTER_BY_RESOURCE_TYPES = enum.auto()
    FILTER_BY_TEMPORAL_EXTENT = enum.auto()
    FILTER_BY_PUBLICATION_DATE = enum.auto()
    FILTER_BY_SPATIAL_EXTENT = enum.auto()
    MODIFY_LAYER_METADATA = enum.auto()
    MODIFY_LAYER_STYLE = enum.auto()
    LOAD_VECTOR_DATASET_VIA_WMS = enum.auto()
    LOAD_VECTOR_DATASET_VIA_WFS = enum.auto()
    LOAD_RASTER_DATASET_VIA_WMS = enum.auto()
    LOAD_RASTER_DATASET_VIA_WCS = enum.auto()


class GeonodeService(enum.Enum):
    OGC_WMS = "wms"
    OGC_WFS = "wfs"
    OGC_WCS = "wcs"
    FILE_DOWNLOAD = "file_download"


class GeonodeResourceType(enum.Enum):
    VECTOR_LAYER = "vector"
    RASTER_LAYER = "raster"
    MAP = "map"


class OrderingType(enum.Enum):
    NAME = "name"


@dataclasses.dataclass
class GeonodePaginationInfo:
    total_records: int
    current_page: int
    page_size: int

    @property
    def total_pages(self):
        try:
            result = math.ceil(self.total_records / self.page_size)
        except ZeroDivisionError:
            result = 1
        return result


@dataclasses.dataclass()
class BriefGeonodeStyle:
    name: str
    sld_url: str


@dataclasses.dataclass()
class BriefDataset:
    pk: int
    uuid: UUID
    name: str
    dataset_sub_type: GeonodeResourceType
    title: str
    abstract: str
    published_date: typing.Optional[dt.datetime]
    spatial_extent: QgsRectangle
    temporal_extent: typing.Optional[typing.List[dt.datetime]]
    srid: QgsCoordinateReferenceSystem
    thumbnail_url: str
    link: str
    detail_url: str
    keywords: typing.List[str]
    category: typing.Optional[str]
    service_urls: typing.Dict[GeonodeService, str]
    default_style: BriefGeonodeStyle


@dataclasses.dataclass()
class Dataset(BriefDataset):
    language: str
    license: str
    constraints: str
    owner: typing.Dict[str, str]
    metadata_author: typing.Dict[str, str]
    styles: typing.List[BriefGeonodeStyle]
    default_style: typing.Optional[QtXml.QDomElement]


# TODO: Remove this in favor of BriefDataset
class BriefGeonodeResource:
    pk: typing.Optional[int]
    uuid: UUID
    name: str
    resource_type: GeonodeResourceType
    title: str
    abstract: str
    published_date: typing.Optional[dt.datetime]
    spatial_extent: QgsRectangle
    temporal_extent: typing.Optional[typing.List[dt.datetime]]
    crs: QgsCoordinateReferenceSystem
    thumbnail_url: str
    api_url: typing.Optional[str]
    gui_url: str
    keywords: typing.List[str]
    category: typing.Optional[str]
    service_urls: typing.Dict[GeonodeService, str]

    def __init__(
        self,
        uuid: UUID,
        name: str,
        resource_type: GeonodeResourceType,
        title: str,
        abstract: str,
        spatial_extent: QgsRectangle,
        crs: QgsCoordinateReferenceSystem,
        thumbnail_url: str,
        gui_url: str,
        pk: typing.Optional[int] = None,
        api_url: typing.Optional[str] = None,
        published_date: typing.Optional[dt.datetime] = None,
        temporal_extent: typing.Optional[typing.List[dt.datetime]] = None,
        keywords: typing.Optional[typing.List[str]] = None,
        category: typing.Optional[str] = None,
        service_urls: typing.Optional[typing.Dict[GeonodeService, str]] = None,
    ):
        self.pk = pk
        self.uuid = uuid
        self.name = name
        self.resource_type = resource_type
        self.title = title
        self.abstract = abstract
        self.spatial_extent = spatial_extent
        self.crs = crs
        self.thumbnail_url = thumbnail_url
        self.api_url = api_url
        self.gui_url = gui_url
        self.published_date = published_date
        self.temporal_extent = temporal_extent
        self.keywords = list(keywords) if keywords is not None else []
        self.category = category
        self.service_urls = dict(service_urls) if service_urls is not None else {}


class GeonodeResource(BriefGeonodeResource):
    language: str
    license: str
    constraints: str
    owner: typing.Dict[str, str]
    metadata_author: typing.Dict[str, str]
    default_style: BriefGeonodeStyle
    styles: typing.List[BriefGeonodeStyle]

    def __init__(
        self,
        language: str,
        license: str,
        constraints: str,
        owner: typing.Dict[str, str],
        metadata_author: typing.Dict[str, str],
        default_style: BriefGeonodeStyle,
        styles: typing.List[BriefGeonodeStyle],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.language = language
        self.license = license
        self.constraints = constraints
        self.owner = owner
        self.metadata_author = metadata_author
        self.default_style = default_style
        self.styles = styles


@dataclasses.dataclass
class GeonodeApiSearchFilters:
    page: typing.Optional[int] = 1
    title: typing.Optional[str] = None
    abstract: typing.Optional[str] = None
    keyword: typing.Optional[typing.List[str]] = None
    topic_category: typing.Optional[IsoTopicCategory] = None
    layer_types: typing.Optional[typing.List[GeonodeResourceType]] = dataclasses.field(
        default_factory=list
    )
    ordering_field: typing.Optional[OrderingType] = None
    reverse_ordering: typing.Optional[bool] = False
    temporal_extent_start: typing.Optional[QtCore.QDateTime] = None
    temporal_extent_end: typing.Optional[QtCore.QDateTime] = None
    publication_date_start: typing.Optional[QtCore.QDateTime] = None
    publication_date_end: typing.Optional[QtCore.QDateTime] = None
    spatial_extent: typing.Optional[qgis.core.QgsRectangle] = None
