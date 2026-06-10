from django.db import connection
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.utils.http import urlencode

from .models import (
    Property,
    Property3DModel,
    PropertyDocument,
    PropertyImage,
    PropertyLayer,
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


def dashboard(request):
    selected_property_id = request.GET.get("property_id")

    if (
        selected_property_id
        and selected_property_id.isdigit()
        and not {"layer", "lon", "lat"}.issubset(request.GET)
    ):
        map_details = get_property_map_details([int(selected_property_id)]).get(
            int(selected_property_id)
        )
        if map_details:
            return redirect(
                "?"
                + urlencode(
                    {
                        "property": map_details["property"] or request.GET.get("property", ""),
                        "layer": map_details["layer"],
                        "property_id": int(selected_property_id),
                        "lon": f"{map_details['lon']:.7f}",
                        "lat": f"{map_details['lat']:.7f}",
                    }
                )
            )

    properties = (
        Property.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch("documents", queryset=PropertyDocument.objects.order_by("-uploaded_at")),
            Prefetch("images", queryset=PropertyImage.objects.order_by("-uploaded_at")),
            Prefetch("videos", queryset=PropertyVideo.objects.order_by("-uploaded_at")),
            Prefetch("models_3d", queryset=Property3DModel.objects.order_by("-uploaded_at")),
            Prefetch("layers", queryset=PropertyLayer.objects.order_by("layer_type", "layer_name")),
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
        property_card.cover_image = next(iter(property_card.images.all()), None)
        property_card.asset_total = (
            len(property_card.documents.all())
            + len(property_card.images.all())
            + len(property_card.videos.all())
            + len(property_card.models_3d.all())
            + len(property_card.layers.all())
        )
        map_details = map_details_by_property_id.get(property_card.property_id)
        if map_details:
            property_card.dashboard_url = "?" + urlencode(
                {
                    "property": map_details["property"] or property_card.name,
                    "layer": map_details["layer"],
                    "property_id": property_card.property_id,
                    "lon": f"{map_details['lon']:.7f}",
                    "lat": f"{map_details['lat']:.7f}",
                }
            )
        else:
            property_card.dashboard_url = "?" + urlencode(
                {
                    "property_id": property_card.property_id,
                    "property": property_card.name,
                }
            )

    context = {
        "properties": property_cards,
        "property_count": len(property_cards),
        "is_property_detail": bool(selected_property_id and selected_property_id.isdigit()),
    }
    return render(request, "dashboard.html", context)
