const GEOSERVER_URL = 'https://purandar-airport.rottengrapes.tech/geoserver';
const GEOSERVER_WORKSPACE = 'mtdc';
const STATE_BOUNDARY_LAYER_NAME = `${GEOSERVER_WORKSPACE}:state_bd`;
const MASTER_LAYER_NAME = `${GEOSERVER_WORKSPACE}:master_mtdc`;
const urlParams = new URLSearchParams(window.location.search);
const selectedPropertyMapData = JSON.parse(
    document.getElementById('selected-property-map-data').textContent
);
const selectedPropertyName = urlParams.get('property') || selectedPropertyMapData?.property || '';
const selectedPropertyLayer = urlParams.get('layer') || selectedPropertyMapData?.layer || '';
const selectedPropertyIdParam = urlParams.get('property_id');
const selectedPropertyId = selectedPropertyIdParam !== null ? Number(selectedPropertyIdParam) : Number(selectedPropertyMapData?.property_id);
const selectedPropertyLon = urlParams.has('lon') ? Number(urlParams.get('lon')) : Number(selectedPropertyMapData?.lon);
const selectedPropertyLat = urlParams.has('lat') ? Number(urlParams.get('lat')) : Number(selectedPropertyMapData?.lat);
const selectedPropertyExtent = Array.isArray(selectedPropertyMapData?.area_extent)
    ? selectedPropertyMapData.area_extent.map((value) => Number(value))
    : null;
const hasSelectedPropertyCoordinate = selectedPropertyName && Number.isFinite(selectedPropertyLon) && Number.isFinite(selectedPropertyLat);
const hasSelectedPropertyExtent = selectedPropertyExtent?.length === 4
    && selectedPropertyExtent.every((value) => Number.isFinite(value))
    && selectedPropertyExtent[0] <= selectedPropertyExtent[2]
    && selectedPropertyExtent[1] <= selectedPropertyExtent[3];
const hasSelectedPropertyId = Number.isInteger(selectedPropertyId);
const hasSelectedProperty = hasSelectedPropertyId || hasSelectedPropertyCoordinate || hasSelectedPropertyExtent;
const stateBoundaryExtent = JSON.parse(
    document.getElementById('state-boundary-extent-data').textContent
);

const googleAttribution = 'Google';
const baseLayers = {
    satellite: new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}',
            attributions: googleAttribution,
            preload: 3
        }),
        preload: Infinity
    }),
    osm: new ol.layer.Tile({
        source: new ol.source.OSM({
            preload: 3
        }),
        preload: Infinity
    }),
    terrain: new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: 'http://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}',
            attributions: googleAttribution,
            preload: 3
        }),
        preload: Infinity
    })
};

const stateBoundarySource = new ol.source.TileWMS({
    url: `${GEOSERVER_URL}/${GEOSERVER_WORKSPACE}/wms`,
    params: {
        LAYERS: STATE_BOUNDARY_LAYER_NAME,
        TILED: true,
        VERSION: '1.1.1',
        FORMAT: 'image/png',
        TRANSPARENT: true
    },
    serverType: 'geoserver',
    crossOrigin: 'anonymous',
    transition: 0
});

const stateBoundaryLayer = new ol.layer.Tile({
    source: stateBoundarySource,
    opacity: 1,
    visible: true,
    zIndex: 5
});

const escapeCqlText = (value) => String(value).replace(/'/g, "''");

const normalizeText = (value) => String(value || '').replace(/\s+/g, ' ').trim();

const buildLayerTokenFilter = (value) => {
    const ignoredTokens = new Set(['kmz', 'kml']);
    const tokens = normalizeText(value)
        .replace(/^\d+[\._\-\s]+/, '')
        .replace(/\.(kmz|kml)$/i, '')
        .split(/[^a-zA-Z0-9]+/)
        .map((token) => token.trim())
        .filter((token) => token.length >= 3 && !ignoredTokens.has(token.toLowerCase()));

    if (tokens.length === 0) {
        return '';
    }

    return tokens
        .map((token) => {
            const escapedToken = escapeCqlText(token);
            return `(layer LIKE '%${escapedToken}%' OR path LIKE '%${escapedToken}%')`;
        })
        .join(' AND ');
};

const buildAreaFilter = () => (
    hasSelectedPropertyId ? `property_id=${selectedPropertyId}` :
    buildLayerTokenFilter(selectedPropertyLayer) ||
    buildLayerTokenFilter(selectedPropertyName)
);

const selectedAreaFilter = hasSelectedProperty ? buildAreaFilter() : '';

const masterMtdcSource = new ol.source.TileWMS({
    url: `${GEOSERVER_URL}/${GEOSERVER_WORKSPACE}/wms`,
    params: {
        LAYERS: MASTER_LAYER_NAME,
        TILED: true,
        VERSION: '1.1.1',
        FORMAT: 'image/png',
        TRANSPARENT: true,
        ...(selectedAreaFilter ? { CQL_FILTER: selectedAreaFilter } : {})
    },
    serverType: 'geoserver',
    crossOrigin: 'anonymous',
    transition: 0
});

const masterMtdcLayer = new ol.layer.Tile({
    source: masterMtdcSource,
    opacity: 1,
    visible: true,
    zIndex: 20
});

const map = new ol.Map({
    target: 'mtdc-map',
    layers: [baseLayers.satellite, stateBoundaryLayer, masterMtdcLayer],
    view: new ol.View({
        center: ol.proj.fromLonLat([76.75, 18.85]),
        zoom: 6
    })
});

const fitStateBoundary = () => {
    if (!stateBoundaryExtent || hasSelectedProperty) {
        return;
    }

    const projectedExtent = ol.proj.transformExtent(
        stateBoundaryExtent,
        'EPSG:4326',
        'EPSG:3857'
    );

    map.getView().fit(projectedExtent, {
        padding: [34, 34, 34, 34],
        maxZoom: 7,
        duration: 0
    });
};

map.once('postrender', fitStateBoundary);

const hoverElement = document.getElementById('mtdc-hover-label');
const hoverOverlay = new ol.Overlay({
    element: hoverElement,
    offset: [14, 0],
    positioning: 'center-left',
    stopEvent: false
});
map.addOverlay(hoverOverlay);

let hoverRequestController = null;
let hoveredPointCoordinate = null;
let hoveredPropertyName = '';
let hoveredLayerName = '';
let hoveredPropertyId = null;

const hideHoverLabel = () => {
    hoverElement.hidden = true;
    hoveredPointCoordinate = null;
    hoveredPropertyName = '';
    hoveredLayerName = '';
    hoveredPropertyId = null;
    hoverOverlay.setPosition(undefined);
};

const extractFeatureName = (payload) => {
    const properties = getFeatureProperties(payload);

    return properties.property_name || properties.name || properties.title || properties.layer || '';
};

const getFeatureProperties = (payload) => {
    if (!payload || !Array.isArray(payload.features) || payload.features.length === 0) {
        return {};
    }

    return payload.features[0].properties || {};
};

const getPayloadProjection = (payload) => {
    const crsName = payload?.crs?.properties?.name || '';
    return crsName.includes('3857') ? 'EPSG:3857' : 'EPSG:4326';
};

const readPayloadFeatures = (payload) => {
    if (!payload || !Array.isArray(payload.features) || payload.features.length === 0) {
        return [];
    }

    return new ol.format.GeoJSON().readFeatures(payload, {
        dataProjection: getPayloadProjection(payload),
        featureProjection: 'EPSG:3857'
    });
};

const getFeatureCenterFromPayload = (payload, fallbackCoordinate) => {
    const features = readPayloadFeatures(payload);
    if (features.length === 0) {
        return fallbackCoordinate;
    }

    return ol.extent.getCenter(features[0].getGeometry().getExtent());
};

const getFeatureInfo = (source, coordinate, layerName, extraParams = {}) => {
    const viewResolution = map.getView().getResolution();
    const infoUrl = source.getFeatureInfoUrl(
        coordinate,
        viewResolution,
        'EPSG:3857',
        {
            INFO_FORMAT: 'application/json',
            FEATURE_COUNT: 1,
            QUERY_LAYERS: layerName,
            BUFFER: 12,
            ...extraParams
        }
    );

    if (!infoUrl) {
        return Promise.resolve(null);
    }

    return fetch(infoUrl).then((response) => {
        if (!response.ok) {
            return null;
        }

        return response.json();
    });
};

const zoomToAreaFeature = (payload, fallbackCoordinate) => {
    if (!payload || !Array.isArray(payload.features) || payload.features.length === 0) {
        if (fallbackCoordinate) {
            map.getView().animate({ center: fallbackCoordinate, zoom: 16, duration: 550 });
        }
        return;
    }

    const features = readPayloadFeatures(payload);

    if (features.length === 0) {
        if (fallbackCoordinate) {
            map.getView().animate({ center: fallbackCoordinate, zoom: 16, duration: 550 });
        }
        return;
    }

    map.getView().fit(features[0].getGeometry().getExtent(), {
        padding: [70, 70, 70, 70],
        duration: 700,
        maxZoom: 20
    });
};

const findAreaFeatureAround = async (centerCoordinate) => {
    const candidateCoordinates = [centerCoordinate];
    const extent = map.getView().calculateExtent(map.getSize());
    const width = ol.extent.getWidth(extent);
    const height = ol.extent.getHeight(extent);

    [0.2, 0.35, 0.5, 0.65, 0.8].forEach((xRatio) => {
        [0.2, 0.35, 0.5, 0.65, 0.8].forEach((yRatio) => {
            candidateCoordinates.push([
                extent[0] + width * xRatio,
                extent[1] + height * yRatio
            ]);
        });
    });

    for (const coordinate of candidateCoordinates) {
        const payload = await getFeatureInfo(masterMtdcSource, coordinate, MASTER_LAYER_NAME);
        const featureCount = payload?.features?.length || 0;

        if (featureCount > 0) {
            return payload;
        }
    }

    return null;
};

const openPropertyDashboard = (featureName, layerName, propertyId, coordinate, targetWindow = null) => {
    if (propertyId === null || propertyId === undefined || propertyId === '' || !Number.isInteger(Number(propertyId))) {
        return;
    }

    const targetUrl = new URL(`/property/${Number(propertyId)}/`, window.location.origin);

    if (targetWindow) {
        targetWindow.location.href = targetUrl.toString();
        return;
    }

    window.open(targetUrl.toString(), '_blank');
};

map.on('pointermove', (event) => {
    if (event.dragging) {
        hideHoverLabel();
        return;
    }

    const viewResolution = map.getView().getResolution();
    const infoUrl = masterMtdcSource.getFeatureInfoUrl(
        event.coordinate,
        viewResolution,
        'EPSG:3857',
        {
            INFO_FORMAT: 'application/json',
            FEATURE_COUNT: 1,
            QUERY_LAYERS: MASTER_LAYER_NAME
        }
    );

    if (!infoUrl) {
        hideHoverLabel();
        return;
    }

    if (hoverRequestController) {
        hoverRequestController.abort();
    }

    hoverRequestController = new AbortController();

    fetch(infoUrl, { signal: hoverRequestController.signal })
        .then((response) => (response.ok ? response.json() : null))
        .then((payload) => {
            const featureName = extractFeatureName(payload);
            if (!featureName) {
                hideHoverLabel();
                return;
            }

            hoverElement.textContent = featureName;
            hoverElement.hidden = false;
            const pointProperties = getFeatureProperties(payload);
            hoveredLayerName = pointProperties.layer || '';
            hoveredPropertyId = pointProperties.property_id ?? null;
            hoveredPropertyName = featureName;
            hoveredPointCoordinate = getFeatureCenterFromPayload(payload, event.coordinate);
            hoverOverlay.setPosition(hoveredPointCoordinate);
        })
        .catch((error) => {
            if (error.name !== 'AbortError') {
                hideHoverLabel();
            }
        });
});

map.getViewport().addEventListener('mouseleave', hideHoverLabel);

map.on('singleclick', (event) => {
    if (hoverElement.hidden || !hoveredPropertyName || !hoveredPointCoordinate) {
        return;
    }

    openPropertyDashboard(hoveredPropertyName, hoveredLayerName, hoveredPropertyId, hoveredPointCoordinate);
});

const fitSelectedPropertyExtent = () => {
    const projectedExtent = ol.proj.transformExtent(
        selectedPropertyExtent,
        'EPSG:4326',
        'EPSG:3857'
    );

    map.getView().fit(projectedExtent, {
        padding: [70, 70, 70, 70],
        duration: 0,
        maxZoom: 20
    });
};

const focusSelectedProperty = (selectedCoordinate = null) => {
    masterMtdcLayer.setVisible(true);

    if (hasSelectedPropertyExtent) {
        fitSelectedPropertyExtent();
        return;
    }

    if (!selectedCoordinate) {
        return;
    }

    map.getView().setCenter(selectedCoordinate);
    map.getView().setZoom(14);

    findAreaFeatureAround(selectedCoordinate)
        .then((payload) => zoomToAreaFeature(payload, selectedCoordinate))
        .catch(() => {
            map.getView().animate({ center: selectedCoordinate, zoom: 16, duration: 550 });
        });
};

if (hasSelectedPropertyExtent) {
    focusSelectedProperty();
} else if (hasSelectedPropertyCoordinate) {
    focusSelectedProperty(ol.proj.fromLonLat([selectedPropertyLon, selectedPropertyLat]));
}

document.querySelectorAll('.layer-options button').forEach((button) => {
    button.addEventListener('click', () => {
        const selectedLayer = baseLayers[button.dataset.layer];
        if (!selectedLayer) return;

        map.getLayers().setAt(0, selectedLayer);
        document.querySelectorAll('.layer-options button').forEach((item) => {
            item.classList.toggle('is-active', item === button);
        });
    });
});

const propertySearchInput = document.getElementById('property-search');
const propertyCards = Array.from(document.querySelectorAll('.asset-card[data-property-id]'));
const propertySearchEmpty = document.getElementById('property-search-empty');
const propertySidebarCount = document.getElementById('property-sidebar-count');
const analyticsTotalProperties = document.getElementById('analytics-total-properties');
const initialPropertyCountLabel = propertySidebarCount?.textContent || '';

propertyCards.forEach((card) => {
    const propertyId = card.dataset.propertyId;
    if (!propertyId) {
        return;
    }
    card.addEventListener('click', () => {
        window.open(`/property/${propertyId}/`, '_blank');
    });
});

const ownershipBreakdownData = JSON.parse(document.getElementById('ownership-breakdown-data').textContent);
const zoneBreakdownData = JSON.parse(document.getElementById('zone-breakdown-data').textContent);

const ownershipBreakdownTitle = document.getElementById('ownership-breakdown-title');
const ownershipBreakdownTable = document.getElementById('ownership-breakdown-table');
const ownershipTiles = Array.from(document.querySelectorAll('.ownership-toggle[data-ownership-metric]'));
const zoneBreakdownTitle = document.getElementById('zone-breakdown-title');
const zoneBreakdownTable = document.getElementById('zone-breakdown-table');
const zoneTiles = Array.from(document.querySelectorAll('.ownership-toggle[data-zone-metric]'));

const renderOwnershipBreakdown = (metric) => {
    const data = ownershipBreakdownData[metric] || ownershipBreakdownData.ppp;

    if (ownershipBreakdownTitle) {
        ownershipBreakdownTitle.textContent = data.title;
    }

    if (!ownershipBreakdownTable) {
        return;
    }

    ownershipBreakdownTable.replaceChildren();

    const rows = (data.rows || []).filter(([, value]) => Number(value) > 0);
    if (!rows.length) {
        const empty = document.createElement('div');
        empty.className = 'analytics-empty';
        empty.textContent = `No ${data.metricLabel} data found.`;
        ownershipBreakdownTable.appendChild(empty);
    } else {
        const header = document.createElement('div');
        header.className = 'ownership-breakdown-head-row';
        header.innerHTML = '<span>Region</span><span>Count</span>';
        ownershipBreakdownTable.appendChild(header);

        rows.forEach(([region, value]) => {
            const row = document.createElement('div');
            row.className = 'ownership-breakdown-row';
            row.innerHTML = '<span class="ownership-breakdown-region">' + region + '</span><span class="ownership-breakdown-value">' + value + '</span>';
            ownershipBreakdownTable.appendChild(row);
        });
    }

    ownershipTiles.forEach((tile) => {
        tile.classList.toggle('is-active', tile.dataset.ownershipMetric === metric);
    });
};

ownershipTiles.forEach((tile) => {
    tile.addEventListener('click', () => renderOwnershipBreakdown(tile.dataset.ownershipMetric));
});

renderOwnershipBreakdown('ppp');

const renderZoneBreakdown = (metric) => {
    const data = zoneBreakdownData[metric] || zoneBreakdownData.rp;

    if (zoneBreakdownTitle) {
        zoneBreakdownTitle.textContent = `${data.title} Breakdown`;
    }

    if (!zoneBreakdownTable) {
        return;
    }

    zoneBreakdownTable.replaceChildren();

    const header = document.createElement('div');
    header.className = 'ownership-breakdown-head-row';
    header.innerHTML = '<span>Zone</span><span>Count</span>';
    zoneBreakdownTable.appendChild(header);

    if (!data.rows.length) {
        const empty = document.createElement('div');
        empty.className = 'analytics-empty';
        empty.textContent = `No ${data.metricLabel} data found.`;
        zoneBreakdownTable.appendChild(empty);
    } else {
        data.rows.forEach(([zone, value]) => {
            const row = document.createElement('div');
            row.className = 'ownership-breakdown-row';
            row.innerHTML = '<span class="ownership-breakdown-region">' + zone + '</span><span class="ownership-breakdown-value">' + value + '</span>';
            zoneBreakdownTable.appendChild(row);
        });
    }

    zoneTiles.forEach((tile) => {
        tile.classList.toggle('is-active', tile.dataset.zoneMetric === metric);
    });
};

zoneTiles.forEach((tile) => {
    tile.addEventListener('click', () => renderZoneBreakdown(tile.dataset.zoneMetric));
});

renderZoneBreakdown('rp');
const analyticsRules = {
    ppp: ['ppp', 'public private partnership'],
    lease: ['lease', 'leased'],
    small: ['small property', 'small properties', 'small'],
    commercial: ['commercial'],
    residential: ['residential'],
    public: ['public zone'],
    'semi-public': ['semi-public', 'semi public', 'semipublic']
};

const normalizeOwnershipMetric = (value) => {
    const text = normalizeText(value || '').toLowerCase();
    if (!text) {
        return '';
    }
    if (text.includes('ppp') || text.includes('public private partnership')) {
        return 'ppp';
    }
    if (text.includes('lease')) {
        return 'lease';
    }
    if (text.includes('small')) {
        return 'small';
    }
    return '';
};

const normalizeZoneValue = (value) => {
    const text = normalizeText(value || '').replace(/\s+/g, ' ').trim();
    if (!text) {
        return '';
    }
    const lowered = text.toLowerCase();
    if (['-', 'null', 'none', 'n/a', 'na', '_', '[]', '[null]'].includes(lowered)) {
        return '';
    }
    if (/^[-_\[\](){}\u2013\u2014\s]+$/.test(text)) {
        return '';
    }
    return text;
};

const getAnalyticsText = (card) => normalizeText(
    ` ${card.dataset.propertyId || ''} ${card.dataset.propertyName || ''} ${card.dataset.propertyLayer || ''} ${card.textContent || ''} `
).toLowerCase();

const hasAnalyticsMatch = (text, key) => {
    if (key === 'public' && hasAnalyticsMatch(text, 'semi-public')) {
        return false;
    }

    return (analyticsRules[key] || []).some((term) => text.includes(term));
};

const setAnalyticsRowValue = (key, value, maxValue) => {
    const row = document.querySelector(`.analytics-row[data-analytics-key="${key}"]`);
    if (!row) {
        return;
    }

    const valueElement = row.querySelector('.analytics-value');
    const meter = row.querySelector('.analytics-meter i');
    const percentage = maxValue > 0 ? Math.round((value / maxValue) * 100) : 0;

    if (valueElement) {
        valueElement.textContent = value;
    }

    if (meter) {
        meter.style.setProperty('--meter', `${percentage}%`);
    }
};

const updateAnalytics = () => {
    const visibleCards = propertyCards.filter((card) => !card.hidden);
    const counts = Object.keys(analyticsRules).reduce((accumulator, key) => {
        accumulator[key] = 0;
        return accumulator;
    }, {});
    const ownershipCounts = {
        ppp: 0,
        lease: 0,
        small: 0
    };
    const zoneCounts = {
        rp: {
            count: 0,
            rows: {}
        },
        dp: {
            count: 0,
            rows: {}
        }
    };

    visibleCards.forEach((card) => {
        const analyticsText = getAnalyticsText(card);
        const ownershipMetric = normalizeOwnershipMetric(card.dataset.propertyCategory || card.dataset.propertyLayer || '');
        const rpZone = normalizeZoneValue(card.dataset.propertyRpZone || '');
        const dpZone = normalizeZoneValue(card.dataset.propertyDpZone || '');

        if (ownershipMetric && Object.prototype.hasOwnProperty.call(ownershipCounts, ownershipMetric)) {
            ownershipCounts[ownershipMetric] += 1;
        }

        Object.keys(counts).forEach((key) => {
            if (hasAnalyticsMatch(analyticsText, key)) {
                counts[key] += 1;
            }
        });

        if (rpZone) {
            zoneCounts.rp.count += 1;
            zoneCounts.rp.rows[rpZone] = (zoneCounts.rp.rows[rpZone] || 0) + 1;
        }

        if (dpZone) {
            zoneCounts.dp.count += 1;
            zoneCounts.dp.rows[dpZone] = (zoneCounts.dp.rows[dpZone] || 0) + 1;
        }
    });

    if (analyticsTotalProperties) {
        analyticsTotalProperties.textContent = visibleCards.length;
    }

    ['commercial', 'residential', 'public', 'semi-public'].forEach((key) => {
        setAnalyticsRowValue(key, counts[key], visibleCards.length);
    });

    ['ppp', 'lease', 'small'].forEach((key) => {
        const tileValue = document.querySelector(`.ownership-tile strong[data-analytics-key="${key}"]`);
        if (tileValue) {
            tileValue.textContent = ownershipCounts[key];
        }
    });

    ['rp', 'dp'].forEach((key) => {
        const zoneCountElement = document.querySelector(`.ownership-tile strong[data-zone-count="${key}"]`);
        if (zoneCountElement) {
            zoneCountElement.textContent = zoneCounts[key].count;
        }

        zoneBreakdownData[key] = {
            ...zoneBreakdownData[key],
            count: zoneCounts[key].count,
            rows: Object.entries(zoneCounts[key].rows).sort((a, b) => {
                if (b[1] !== a[1]) {
                    return b[1] - a[1];
                }
                return a[0].localeCompare(b[0]);
            })
        };
    });

    const activeZoneMetric = zoneTiles.find((tile) => tile.classList.contains('is-active'))?.dataset.zoneMetric || 'rp';
    renderZoneBreakdown(activeZoneMetric);
};

const filterPropertyCards = () => {
    const query = normalizeText(propertySearchInput?.value || '').toLowerCase();
    let visibleCount = 0;

    propertyCards.forEach((card) => {
        const searchableText = `${card.dataset.propertyId || ''} ${card.dataset.propertyName || ''} ${card.dataset.propertyLayer || ''}`.toLowerCase();
        const isMatch = !query || searchableText.includes(query);
        card.hidden = !isMatch;
        if (isMatch) {
            visibleCount += 1;
        }
    });

    if (propertySearchEmpty) {
        propertySearchEmpty.hidden = visibleCount !== 0;
    }

    if (propertySidebarCount) {
        propertySidebarCount.textContent = query
            ? `${visibleCount} ${visibleCount === 1 ? 'property' : 'properties'} matched`
            : initialPropertyCountLabel;
    }

    updateAnalytics();
};

if (propertySearchInput) {
    propertySearchInput.addEventListener('input', filterPropertyCards);
}

updateAnalytics();

const assetModal = document.getElementById('asset-viewer-modal');
const assetModalTitle = document.getElementById('asset-modal-title');
const assetModalSubtitle = document.getElementById('asset-modal-subtitle');
const assetModalSearch = document.getElementById('asset-modal-search');
const assetModalList = document.getElementById('asset-modal-list');
const assetViewerTitle = document.getElementById('asset-viewer-title');
const assetViewerStage = document.getElementById('asset-viewer-stage');
const assetModalClose = document.getElementById('asset-modal-close');
const assetPrevBtn = document.getElementById('asset-prev-btn');
const assetNextBtn = document.getElementById('asset-next-btn');
const assetCategoryLabels = {
    documents: 'Documents',
    images: 'Images',
    videos: 'Videos',
    models3d: '3D Models'
};
const assetCategoryIcons = {
    documents: 'description',
    images: 'image',
    videos: 'movie',
    models3d: 'deployed_code'
};
let activeAssetItems = [];
let activeAssetIndex = -1;
let activeAssetCategory = '';

const getAssetItems = (propertyId, category) => {
    const propertyData = document.querySelector(`.property-asset-data[data-property-id="${Number(propertyId)}"]`);
    if (!propertyData) {
        return [];
    }

    return Array.from(propertyData.querySelectorAll(`.asset-data-item[data-category="${category}"]`)).map((item) => ({
        category,
        group: item.dataset.group || assetCategoryLabels[category],
        kind: item.dataset.kind || category,
        title: item.dataset.title || 'Untitled asset',
        url: item.dataset.url || ''
    }));
};

const getFileExtension = (url) => {
    const cleanUrl = String(url || '').split('?')[0].split('#')[0];
    const extension = cleanUrl.includes('.') ? cleanUrl.split('.').pop() : '';
    return extension.toLowerCase();
};

const renderAssetEmptyState = (message) => {
    assetViewerStage.replaceChildren();
    assetViewerStage.className = 'asset-viewer-stage';
    const empty = document.createElement('div');
    empty.className = 'asset-viewer-empty';
    empty.textContent = message;
    assetViewerStage.appendChild(empty);
};

const updateAssetNav = () => {
    const canNavigate = ['images', 'models3d'].includes(activeAssetCategory) && activeAssetItems.length > 1;
    assetPrevBtn.hidden = !canNavigate;
    assetNextBtn.hidden = !canNavigate;
};

const renderAssetViewer = (index) => {
    activeAssetIndex = index;
    const item = activeAssetItems[index];

    assetModalList.querySelectorAll('.asset-modal-item').forEach((button, buttonIndex) => {
        button.classList.toggle('is-active', buttonIndex === index);
    });

    if (!item) {
        assetViewerTitle.textContent = 'Select an item';
        renderAssetEmptyState('Select an item from the left panel.');
        updateAssetNav();
        return;
    }

    assetViewerTitle.textContent = item.title;
    assetViewerStage.replaceChildren();
    assetViewerStage.className = `asset-viewer-stage is-${item.kind}`;

    if (item.kind === 'image') {
        const image = document.createElement('img');
        image.src = item.url;
        image.alt = item.title;
        assetViewerStage.appendChild(image);
    } else if (item.kind === 'video') {
        const video = document.createElement('video');
        video.src = item.url;
        video.controls = true;
        video.playsInline = true;
        assetViewerStage.appendChild(video);
    } else if (item.kind === 'model') {
        const extension = getFileExtension(item.url);
        if (['glb', 'gltf'].includes(extension)) {
            const modelViewer = document.createElement('model-viewer');
            modelViewer.src = item.url;
            modelViewer.alt = item.title;
            modelViewer.setAttribute('camera-controls', '');
            modelViewer.setAttribute('auto-rotate', '');
            modelViewer.setAttribute('shadow-intensity', '0.6');
            assetViewerStage.appendChild(modelViewer);
        } else {
            const fallback = document.createElement('div');
            fallback.className = 'asset-viewer-empty';
            fallback.append(
                document.createTextNode('Preview is not available for this 3D file.'),
                document.createElement('br'),
                document.createElement('br')
            );
            const link = document.createElement('a');
            link.href = item.url;
            link.target = '_blank';
            link.rel = 'noopener';
            link.textContent = 'Open or download 3D file';
            fallback.appendChild(link);
            assetViewerStage.appendChild(fallback);
        }
    } else {
        const extension = getFileExtension(item.url);
        if (extension === 'pdf') {
            const frame = document.createElement('iframe');
            frame.src = item.url;
            frame.title = item.title;
            assetViewerStage.appendChild(frame);
        } else {
            const fallback = document.createElement('div');
            fallback.className = 'asset-viewer-empty';
            fallback.append(
                document.createTextNode('Preview is not available for this file.'),
                document.createElement('br'),
                document.createElement('br')
            );
            const link = document.createElement('a');
            link.href = item.url;
            link.target = '_blank';
            link.rel = 'noopener';
            link.textContent = 'Open or download file';
            fallback.appendChild(link);
            assetViewerStage.appendChild(fallback);
        }
    }

    updateAssetNav();
};

const renderAssetList = () => {
    const query = normalizeText(assetModalSearch.value).toLowerCase();
    const filteredItems = activeAssetItems.filter((item) => (
        !query ||
        item.title.toLowerCase().includes(query) ||
        item.group.toLowerCase().includes(query)
    ));
    let currentGroup = '';

    assetModalList.replaceChildren();

    if (filteredItems.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'asset-viewer-empty';
        empty.textContent = 'No matching assets found.';
        assetModalList.appendChild(empty);
        renderAssetEmptyState('No matching assets found.');
        return;
    }

    filteredItems.forEach((item) => {
        const originalIndex = activeAssetItems.indexOf(item);
        if (item.group !== currentGroup) {
            currentGroup = item.group;
            const group = document.createElement('div');
            group.className = 'asset-modal-group';
            group.textContent = currentGroup;
            assetModalList.appendChild(group);
        }

        const button = document.createElement('button');
        button.className = 'asset-modal-item';
        button.type = 'button';
        const icon = document.createElement('span');
        icon.className = 'material-symbols-outlined';
        icon.textContent = assetCategoryIcons[item.category];
        const title = document.createElement('span');
        title.textContent = item.title;
        button.append(icon, title);
        button.addEventListener('click', () => renderAssetViewer(originalIndex));
        assetModalList.appendChild(button);
    });

    const selectedIndex = filteredItems.includes(activeAssetItems[activeAssetIndex])
        ? activeAssetIndex
        : activeAssetItems.indexOf(filteredItems[0]);
    renderAssetViewer(selectedIndex);
};

const openAssetModal = (propertyId, category) => {
    const propertyData = document.querySelector(`.property-asset-data[data-property-id="${Number(propertyId)}"]`);
    const propertyName = propertyData?.dataset.propertyName || 'Selected property';
    activeAssetCategory = category;
    activeAssetItems = getAssetItems(propertyId, category);
    activeAssetIndex = -1;

    assetModalTitle.textContent = assetCategoryLabels[category] || 'Assets';
    assetModalSubtitle.textContent = `${propertyName} - ${activeAssetItems.length} ${activeAssetItems.length === 1 ? 'item' : 'items'}`;
    assetModalSearch.value = '';
    assetModal.hidden = false;
    document.body.style.overflow = 'hidden';
    renderAssetList();
    assetModalSearch.focus();
};

const closeAssetModal = () => {
    assetModal.hidden = true;
    document.body.style.overflow = '';
    assetViewerStage.replaceChildren();
    assetModalList.replaceChildren();
    activeAssetItems = [];
    activeAssetIndex = -1;
    activeAssetCategory = '';
};

document.querySelectorAll('.asset-view-btn').forEach((button) => {
    button.addEventListener('click', () => {
        openAssetModal(button.dataset.propertyId, button.dataset.category);
    });
});

assetModalSearch.addEventListener('input', renderAssetList);
assetModalClose.addEventListener('click', closeAssetModal);
assetPrevBtn.addEventListener('click', () => {
    if (activeAssetItems.length === 0) return;
    const nextIndex = (activeAssetIndex - 1 + activeAssetItems.length) % activeAssetItems.length;
    renderAssetViewer(nextIndex);
});
assetNextBtn.addEventListener('click', () => {
    if (activeAssetItems.length === 0) return;
    const nextIndex = (activeAssetIndex + 1) % activeAssetItems.length;
    renderAssetViewer(nextIndex);
});
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !assetModal.hidden) {
        closeAssetModal();
    }
});
document.querySelectorAll('[data-property-tabs]').forEach((tabGroup) => {
    const tabs = Array.from(tabGroup.querySelectorAll('[data-property-tab]'));
    const panels = Array.from(tabGroup.querySelectorAll('[data-property-panel]'));

    const activateTab = (activeTab) => {
        const activeKey = activeTab.dataset.propertyTab;

        tabs.forEach((tab) => {
            const isActive = tab === activeTab;
            tab.classList.toggle('is-active', isActive);
            tab.setAttribute('aria-selected', String(isActive));
        });

        panels.forEach((panel) => {
            const isActive = panel.dataset.propertyPanel === activeKey;
            panel.classList.toggle('is-active', isActive);
            panel.hidden = !isActive;
        });
    };

    tabs.forEach((tab) => {
        tab.addEventListener('click', () => activateTab(tab));
    });
});