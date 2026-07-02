# Sources

## Air-cooling electricity per dwelling

- Source: ODYSSEE/Enerdata export, retrieved 2026-07-02.
- Workbook: `Enerdata_Odyssee_260702_122358.xlsx`.
- ODYSSEE database: https://www.indicators.odyssee-mure.eu/energy-efficiency-database.html
- Indicator reference: https://www.odyssee-mure.eu/publications/efficiency-by-sector/households/unit-consumption-air-conditioning.html

## Map boundaries

- Source: Eurostat GISCO Countries 2024, EPSG:3035.
- GeoJSON used by the script: https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/CNTR_RG_10M_2024_3035.geojson
- GISCO country files: https://gisco-services.ec.europa.eu/distribution/v1/countries-2024.html
- EPSG:3035 reference: https://epsg.io/3035

## Barrier 1: owner-occupied tenure

- Source: Eurostat `ilc_lvho02`, DOI 10.2908/ilc_lvho02.
- Metric used: total renter population share; owner share is computed as `100 - pct_tenant_total`.
- Filters: frequency `A`, income group `TOTAL`, household composition `TOTAL`, tenure `RENT`, unit `PC`.
- Eurostat table: https://ec.europa.eu/eurostat/databrowser/view/ilc_lvho02/default/table?lang=en
- Direct CSV: https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/ilc_lvho02/A.TOTAL.TOTAL.RENT.PC.?format=SDMX-CSV&startPeriod=2024
- Local file: `barrier1_tenant_landlord.csv`.

## Barrier 3: building-stock age

- Source: Eurostat `cens_21dwop_r3`, DOI 10.2908/cens_21dwop_r3, 2021 Population & Housing Census.
- Metric used: conventional dwellings by construction period.
- Filters: housing `DW`, unit `NR`, country-level geographies.
- Pre-1980 share uses `before_1919 + y1919_1945 + y1946_1960 + y1961_1980`.
- The known-stock denominator excludes dwellings with unknown construction year.
- Eurostat table: https://ec.europa.eu/eurostat/databrowser/view/cens_21dwop_r3/default/table?lang=en
- Direct CSV: https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/cens_21dwop_r3/A.DW..NR.DE+FR+ES+IT+NL+BE+AT+LU+DK+SE+FI+IE+PT+EL+CY+MT+HR+BG+CZ+EE+HU+LV+LT+PL+RO+SI+SK+CH+NO+IS+LI?format=SDMX-CSV
- Local file: `barrier3_building_age.csv`.
