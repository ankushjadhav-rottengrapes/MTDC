from django.db import connection
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import (
    Property,
    Property3DModel,
    PropertyDocument,
    PropertyImage,
    PropertyVideo,
)


def get_property_map_details(property_ids):
    property_ids = list(property_ids)
    if not property_ids:
        return {}

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                property_id,
                name,
                layer,
                ST_X(ST_Transform(geom, 4326)) AS lon,
                ST_Y(ST_Transform(geom, 4326)) AS lat
            FROM public.pt_mtdc
            WHERE property_id = ANY(%s)
            """,
            [property_ids],
        )
        return {
            row[0]: {
                "property": row[1] or "",
                "layer": row[2] or "",
                "lon": row[3],
                "lat": row[4],
            }
            for row in cursor.fetchall()
        }


def get_state_boundary_extent():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ST_XMin(ST_Extent(ST_Transform(geom, 4326))) AS min_lon,
                ST_YMin(ST_Extent(ST_Transform(geom, 4326))) AS min_lat,
                ST_XMax(ST_Extent(ST_Transform(geom, 4326))) AS max_lon,
                ST_YMax(ST_Extent(ST_Transform(geom, 4326))) AS max_lat
            FROM public.state_bd
            """
        )
        extent = cursor.fetchone()

    if not extent or any(value is None for value in extent):
        return None

    return {
        "min_lon": extent[0],
        "min_lat": extent[1],
        "max_lon": extent[2],
        "max_lat": extent[3],
    }


@login_required
def dashboard(request, property_id=None):
    selected_property_id = str(property_id) if property_id is not None else request.GET.get("property_id")

    if property_id is None and selected_property_id and selected_property_id.isdigit():
        return redirect(f"/property/{int(selected_property_id)}/")

    properties = (
        Property.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch("documents", queryset=PropertyDocument.objects.order_by("-uploaded_at")),
            Prefetch("images", queryset=PropertyImage.objects.order_by("-uploaded_at")),
            Prefetch("videos", queryset=PropertyVideo.objects.order_by("-uploaded_at")),
            Prefetch("models_3d", queryset=Property3DModel.objects.order_by("-uploaded_at")),
        )
        .order_by("property_id")
    )

    if selected_property_id and selected_property_id.isdigit():
        properties = properties.filter(property_id=int(selected_property_id))

    property_cards = list(properties)
    map_details_by_property_id = get_property_map_details(
        property_card.property_id for property_card in property_cards
    )

    for property_card in property_cards:
        property_card.asset_total = (
            len(property_card.documents.all())
            + len(property_card.images.all())
            + len(property_card.videos.all())
            + len(property_card.models_3d.all())
        )
        map_details = map_details_by_property_id.get(property_card.property_id)
        property_card.map_layer = map_details["layer"] if map_details else ""
        property_card.dashboard_url = f"/property/{property_card.property_id}/"

    selected_property_map_details = None
    if selected_property_id and selected_property_id.isdigit():
        selected_property_map_details = map_details_by_property_id.get(
            int(selected_property_id)
        )
        if selected_property_map_details:
            selected_property_map_details = {
                "property": (
                    selected_property_map_details["property"]
                    or (property_cards[0].name if property_cards else "")
                ),
                "layer": selected_property_map_details["layer"],
                "property_id": int(selected_property_id),
                "lon": selected_property_map_details["lon"],
                "lat": selected_property_map_details["lat"],
            }

    state_boundary_extent = get_state_boundary_extent()
    state_boundary_extent_coords = (
        [
            state_boundary_extent["min_lon"],
            state_boundary_extent["min_lat"],
            state_boundary_extent["max_lon"],
            state_boundary_extent["max_lat"],
        ]
        if state_boundary_extent
        else None
    )

    context = {
        "properties": property_cards,
        "property_count": len(property_cards),
        "is_property_detail": bool(selected_property_id and selected_property_id.isdigit()),
        "state_boundary_extent_coords": state_boundary_extent_coords,
        "selected_property_map_details": selected_property_map_details,
    }
    return render(request, "dashboard.html", context)
