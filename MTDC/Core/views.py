import binascii
import struct

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import master_mtdc, PropertyCover, PropertyImage, PropertyDocument, PropertyVideo


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
    selected_property_map_details = None

    if selected_property_id and selected_property_id.isdigit():
        selected_property_id_int = int(selected_property_id)
        properties = properties.filter(property_id=selected_property_id_int)
        selected_property_obj = properties.first()
        selected_property_map_details = _build_selected_property_map_data(selected_property_obj)

    property_cards = list(properties)

    covers = PropertyCover.objects.filter(
        property_id__in=[p.property_id for p in property_cards]
    )
    cover_map = {c.property_id: c.cover_image.url for c in covers}

    for prop in property_cards:
        prop.cover_url = cover_map.get(prop.property_id)

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
    }
    return render(request, "dashboard.html", context)