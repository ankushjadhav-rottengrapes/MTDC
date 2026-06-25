import binascii
import re
import struct
from collections import Counter

from django.db import connection
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import master_mtdc, PropertyCover, PropertyImage, PropertyDocument, PropertyVideo

OWNERSHIP_REGION_ORDER = [
    "Ratnagiri",
    "Pune",
    "Nashik",
    "Raigad",
    "Nagpur",
    "Thane",
    "Dharashiv",
    "Hingoli",
]


def _normalize_ownership_category(category):
    value = (category or "").strip().lower()
    if not value:
        return ""
    if "ppp" in value or "public private partnership" in value:
        return "ppp"
    if "lease" in value:
        return "lease"
    if "small" in value:
        return "small"
    return value


def _build_ownership_data(properties):
    metrics = {
        "ppp": {"title": "PPP", "metricLabel": "PPP", "count": 0, "regions": Counter()},
        "lease": {"title": "Lease Renewal", "metricLabel": "Lease Renewal", "count": 0, "regions": Counter()},
        "small": {"title": "Small Properties", "metricLabel": "Small Properties", "count": 0, "regions": Counter()},
    }

    extra_regions = []
    for prop in properties:
        metric = _normalize_ownership_category(getattr(prop, "category", ""))
        if metric not in metrics:
            continue

        region = (getattr(prop, "region", "") or "").strip()
        if not region:
            region = "Unspecified"
        metrics[metric]["count"] += 1
        metrics[metric]["regions"][region] += 1
        if region not in OWNERSHIP_REGION_ORDER and region not in extra_regions and region != "Unspecified":
            extra_regions.append(region)

    ordered_regions = OWNERSHIP_REGION_ORDER + sorted(extra_regions)
    if any(metric["regions"].get("Unspecified") for metric in metrics.values()):
        ordered_regions.append("Unspecified")

    breakdown = {}
    for key, metric in metrics.items():
        breakdown[key] = {
            "title": metric["title"],
            "metricLabel": metric["metricLabel"],
            "count": metric["count"],
            "rows": [[region, metric["regions"].get(region, 0)] for region in ordered_regions],
        }

    return breakdown


def _display_ownership_category(category):
    metric = _normalize_ownership_category(category)
    return {
        "ppp": "PPP",
        "lease": "Lease Renewal",
        "small": "Small Properties",
    }.get(metric, category or "")


def _normalize_zone_value(zone):
    value = re.sub(r"\s+", " ", (zone or "")).strip()
    if not value or value == "-":
        return ""
    return value


def _zone_key(zone):
    value = _normalize_zone_value(zone).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _build_zone_breakdown_data(properties):
    breakdown = {
        "rp": {"title": "RP Zone", "metricLabel": "RP Zone", "count": 0, "zones": Counter()},
        "dp": {"title": "DP Zone", "metricLabel": "DP Zone", "count": 0, "zones": Counter()},
    }

    for prop in properties:
        rp_zone = _normalize_zone_value(getattr(prop, "rp_zone", ""))
        dp_zone = _normalize_zone_value(getattr(prop, "dp_zone", ""))

        if rp_zone:
            breakdown["rp"]["count"] += 1
            breakdown["rp"]["zones"][rp_zone] += 1

        if dp_zone:
            breakdown["dp"]["count"] += 1
            breakdown["dp"]["zones"][dp_zone] += 1

    for key, metric in breakdown.items():
        sorted_rows = sorted(
            metric["zones"].items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
        breakdown[key] = {
            "title": metric["title"],
            "metricLabel": metric["metricLabel"],
            "count": metric["count"],
            "rows": [[zone, count] for zone, count in sorted_rows],
        }

    return breakdown


def _fetch_region_property_counts():
    query = """
        SELECT
            BTRIM(region) AS region,
            COUNT(DISTINCT property_id) AS property_count
        FROM public.mtdc_pdf_data
        WHERE NULLIF(BTRIM(region), '') IS NOT NULL
        GROUP BY BTRIM(region)
        ORDER BY BTRIM(region);
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    region_property_counts = [
        {
            "region": row[0],
            "property_count": int(row[1]),
        }
        for row in rows
    ]

    max_region_property_count = max((item["property_count"] for item in region_property_counts), default=0)

    return region_property_counts, max(max_region_property_count, 1)


def _read_wkb_uint32(raw, offset, endian):
    return struct.unpack(endian + 'I', raw[offset:offset + 4])[0]


def _read_wkb_double(raw, offset, endian):
    return struct.unpack(endian + 'd', raw[offset:offset + 8])[0]


def _extract_wkb_coordinates(raw, offset=0):
    if offset + 5 > len(raw):
        return [], offset

    byte_order = raw[offset]
    endian = '<' if byte_order == 1 else '>'
    geom_type = _read_wkb_uint32(raw, offset + 1, endian)
    has_z = bool(geom_type & 0x80000000)
    has_srid = bool(geom_type & 0x20000000)
    type_code = geom_type & 0xFFFF
    ptr = offset + 5

    if has_srid:
        ptr += 4

    def read_point(p):
        x = _read_wkb_double(raw, p, endian)
        y = _read_wkb_double(raw, p + 8, endian)
        if has_z:
            return (x, y), p + 24
        return (x, y), p + 16

    if type_code == 1:
        point, ptr = read_point(ptr)
        return [point], ptr

    if type_code == 2:
        count = _read_wkb_uint32(raw, ptr, endian)
        ptr += 4
        coords = []
        for _ in range(count):
            point, ptr = read_point(ptr)
            coords.append(point)
        return coords, ptr

    if type_code == 3:
        ring_count = _read_wkb_uint32(raw, ptr, endian)
        ptr += 4
        coords = []
        for _ in range(ring_count):
            point_count = _read_wkb_uint32(raw, ptr, endian)
            ptr += 4
            for _ in range(point_count):
                point, ptr = read_point(ptr)
                coords.append(point)
        return coords, ptr

    if type_code in {4, 5, 6, 7}:
        child_count = _read_wkb_uint32(raw, ptr, endian)
        ptr += 4
        coords = []
        for _ in range(child_count):
            child_coords, ptr = _extract_wkb_coordinates(raw, ptr)
            coords.extend(child_coords)
        return coords, ptr

    return [], ptr


def _parse_wkb_extent(wkb_hex):
    if not wkb_hex:
        return None

    try:
        raw = binascii.unhexlify(wkb_hex)
    except (TypeError, ValueError):
        return None

    coords, _ = _extract_wkb_coordinates(raw)
    if not coords:
        return None

    xs = [x for x, y in coords]
    ys = [y for x, y in coords]
    return [min(xs), min(ys), max(xs), max(ys)]


def _parse_wkb_point(wkb_hex):
    if not wkb_hex:
        return None

    try:
        raw = binascii.unhexlify(wkb_hex)
    except (TypeError, ValueError):
        return None

    coords, _ = _extract_wkb_coordinates(raw)
    return coords[0] if coords else None


def _build_selected_property_map_data(property_obj):
    if not property_obj:
        return None

    extent = None
    for source in (property_obj.poly_geom, property_obj.pl_geom, property_obj.pt_geom, property_obj.centroid):
        extent = _parse_wkb_extent(source)
        if extent:
            break

    coordinate = _parse_wkb_point(property_obj.centroid) or _parse_wkb_point(property_obj.pt_geom)
    if not coordinate and extent:
        coordinate = ((extent[0] + extent[2]) / 2, (extent[1] + extent[3]) / 2)

    return {
        'property_id': property_obj.property_id,
        'property': property_obj.property_name,
        'layer': property_obj.property_name,
        'lon': coordinate[0] if coordinate else None,
        'lat': coordinate[1] if coordinate else None,
        'area_extent': extent,
    }


@login_required
def dashboard(request, property_id=None):
    selected_property_id = str(property_id) if property_id is not None else request.GET.get("property_id")

    if property_id is None and selected_property_id and selected_property_id.isdigit():
        return redirect(f"/property/{int(selected_property_id)}/")

    properties = master_mtdc.objects.all().order_by("property_id")
    property_cards = list(properties)
    ownership_breakdown_data = _build_ownership_data(property_cards)
    zone_breakdown_data = _build_zone_breakdown_data(property_cards)
    selected_property_map_details = None
    region_property_counts, max_region_property_count = _fetch_region_property_counts()

    if selected_property_id and selected_property_id.isdigit():
        selected_property_id_int = int(selected_property_id)
        properties = properties.filter(property_id=selected_property_id_int)
        selected_property_obj = properties.first()
        selected_property_map_details = _build_selected_property_map_data(selected_property_obj)

    covers = PropertyCover.objects.filter(
        property_id__in=[p.property_id for p in property_cards]
    )
    cover_map = {c.property_id: c.cover_image.url for c in covers}

    for prop in property_cards:
        prop.cover_url = cover_map.get(prop.property_id)
        prop.display_category = _display_ownership_category(getattr(prop, "category", ""))

    property_images = []
    property_documents = []
    property_videos = []

    if selected_property_id and selected_property_id.isdigit():
        pid = int(selected_property_id)
        property_images = list(PropertyImage.objects.filter(property_id=pid))
        property_documents = list(PropertyDocument.objects.filter(property_id=pid))
        property_videos = list(PropertyVideo.objects.filter(property_id=pid))

    context = {
        "properties": property_cards,
        "property_count": len(property_cards),
        "is_property_detail": bool(selected_property_id and selected_property_id.isdigit()),
        "state_boundary_extent_coords": None,
        "selected_property_map_details": selected_property_map_details,
        "property_images": property_images,
        "property_documents": property_documents,
        "property_videos": property_videos,
        "region_property_counts": region_property_counts,
        "max_region_property_count": max_region_property_count,
        "ownership_breakdown_data": ownership_breakdown_data,
        "zone_breakdown_data": zone_breakdown_data,
    }
    return render(request, "dashboard.html", context)
