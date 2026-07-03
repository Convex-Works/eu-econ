# EU Air-Cooling Electricity Figures

Clean figures from the ODYSSEE/Enerdata export on electricity unit consumption per dwelling for air cooling.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_figures.py
```

## Method

The air-cooling electricity source workbook is `Enerdata_Odyssee_260702_122358.xlsx`. Values marked `n.a.` are treated as missing and numeric zeroes are kept.

Shared figure styling is defined in `scripts/figure_style.py`. Chart-specific layout choices remain in `scripts/build_figures.py`.

The 2010/2024 country comparison uses countries with complete annual data from 2010 through 2024 and nonzero 2024 values. Each row shows the 2010 value, the 2024 value, and the absolute change, sorted by the 2024 value.

The map uses every country with a numeric 2024 value in the workbook. Country boundaries are Eurostat GISCO 2024 regions in EPSG:3035.

The tenure and building-stock figures use `barrier1_tenant_landlord.csv` and `barrier3_building_age.csv`. They cover the complete-history comparison countries plus Switzerland, Denmark, and Sweden. The tenure figure shows a two-part population split: owner and renter. The building-age figure splits known construction-year dwellings into pre-1980 and 1981+ stock.

## Sources

- ODYSSEE database: https://www.indicators.odyssee-mure.eu/energy-efficiency-database.html
- ODYSSEE air-conditioning per dwelling indicator: https://www.odyssee-mure.eu/publications/efficiency-by-sector/households/unit-consumption-air-conditioning.html
- Eurostat GISCO Countries 2024: https://gisco-services.ec.europa.eu/distribution/v1/countries-2024.html
- EPSG:3035 ETRS89-LAEA Europe: https://epsg.io/3035
- Eurostat tenure status, ilc_lvho02: https://ec.europa.eu/eurostat/databrowser/view/ilc_lvho02/default/table?lang=en
- Eurostat conventional dwellings by construction period, cens_21dwop_r3: https://ec.europa.eu/eurostat/databrowser/view/cens_21dwop_r3/default/table?lang=en
- Exact Eurostat API links and filters: `SOURCES.md`
