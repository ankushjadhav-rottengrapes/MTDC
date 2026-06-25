# mtdc_pdf_data — Table Reference

## Columns

| Column | Data Type | Notes |
|--------|-----------|-------|
| property_id | integer | FK to `master_mtdc.property_id` |
| Property Type/Categ ory | text | e.g. PPP, Lease, Small |
| name to match | text | Internal name used for layer matching |
| Property Name | text | Property name (Marathi) |
| Village Name | text | Village (Marathi) |
| Taluka | text | Taluka name (Marathi) |
| region | text | Region — `Pune`, `Mumbai`, `Nashik`, `Nagpur` |
| Sr.No | text | Survey number(s), comma-separated |
| Sr.No.1 | text | Primary survey number |
| Area In (Ha.) | double precision | Area in Hectares |
| Area In (Acre) | double precision | Area in Acres |
| RP Zone | text | Regional Plan Zone (e.g. Afforestation Zone) |
| DP Zone | text | Development Plan Zone |
| Basic FSI | text | FSI values as text (e.g. `0.10 / 0.15 / 0.20`) |
| FSI Statements_Permissible Area for Tourist Resort as per Basic | text | Permissible FSI value |
| Note;- (Basic FSI as per applicable UDCPR and local planning au | text | Notes on FSI |
| Permissible Use | text | Regulation details |
| Appropriate Authority / Planning Authority | text | e.g. Town Planning Dept – Pune Regional Plan |
| Valuation_Ready Reckoner Rates (2025-2026)_Valuation_Ready Reck | double precision | RR Rate |
| Valuation_Per Ha | double precision | Value per Hectare |
| Valuation_Total Cost of Land Lakh | double precision | Total land cost in Lakhs |
| Valuation_Final Cost In Lakh | double precision | Final cost in Lakhs |

## Sample Row

| Column | Value |
|--------|-------|
| property_id | 33 |
| Property Type/Categ ory | PPP |
| name to match | 3_Bhimashankar kmz |
| Property Name | भिमाशंकर |
| Village Name | राजपुर |
| Taluka | आंबेगाव |
| region | Pune |
| Sr.No | 196, 197 |
| Sr.No.1 | 196 |
| Area In (Ha.) | 1.01 |
| Area In (Acre) | 2.5 |
| RP Zone | Afforestation Zone |
| DP Zone | _ |
| Basic FSI | (0.10 / 0.15 / 0.20) |
| FSI Statements_Permissible Area | 0.2 |
| Permissible Use | UDCPR Regulation 4.16 read with Regulation 4.11(2)(xv), (xvi), (xxxiii), (xxxiv) |
| Appropriate Authority | Town Planning Dept – Pune Regional Plan |
| Valuation_Per Ha | 308000.0 |
| Valuation_Total Cost of Land Lakh | 311080.0 |
| Valuation_Final Cost In Lakh | 1244320.0 |

## Regions Present

| Region | Description |
|--------|-------------|
| Pune | Pune division properties |
| Mumbai | Mumbai / Konkan division properties |
| Nashik | Nashik division properties |
| Nagpur | Nagpur / Vidarbha division properties |

## Key Relations

- `property_id` → `master_mtdc.property_id` (join key)
- `region` → used for Region Wise Properties analytics on dashboard
- `Property Type/Categ ory` → used for Ownership Details (PPP / Lease / Small)
