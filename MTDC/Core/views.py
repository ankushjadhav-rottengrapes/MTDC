from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import master_mtdc, PropertyCover


@login_required
def dashboard(request, property_id=None):
    selected_property_id = str(property_id) if property_id is not None else request.GET.get("property_id")

    if property_id is None and selected_property_id and selected_property_id.isdigit():
        return redirect(f"/property/{int(selected_property_id)}/")

    properties = master_mtdc.objects.all().order_by("property_id")

    if selected_property_id and selected_property_id.isdigit():
        properties = properties.filter(property_id=int(selected_property_id))

    property_cards = list(properties)

    covers = PropertyCover.objects.filter(
        property_id__in=[p.property_id for p in property_cards]
    )
    cover_map = {c.property_id: c.cover_image.url for c in covers}

    for prop in property_cards:
        prop.cover_url = cover_map.get(prop.property_id)

    context = {
        "properties": property_cards,
        "property_count": len(property_cards),
        "is_property_detail": bool(selected_property_id and selected_property_id.isdigit()),
        "state_boundary_extent_coords": None,
        "selected_property_map_details": None,
    }
    return render(request, "dashboard.html", context)
