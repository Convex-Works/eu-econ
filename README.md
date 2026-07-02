# EU Air-Cooling Opportunity Figures

Clean figures from the ODYSSEE/Enerdata export on electricity unit consumption per dwelling for air cooling.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_figures.py
```

## Outputs

- `figures/air_cooling_opportunity_segments.png`
- `figures/air_cooling_opportunity_segments.svg`
- `figures/air_cooling_2024_map.png`
- `figures/air_cooling_2024_map.svg`

## Method

The source workbook is `Enerdata_Odyssee_260702_122358.xlsx`. Values marked `n.a.` are treated as missing and numeric zeroes are kept.

The segment graph uses countries with complete annual data from 2010 through 2024. The map uses every country with a numeric 2024 value.

Segments are assigned from the complete-history dataset using 2024 consumption and 2010–2024 change:

- Large current market: top quartile by 2024 kWh per dwelling
- Fast riser: not large current market and top quartile by absolute increase
- Emerging opportunity: above median by 2024 level or increase
- Low signal: remaining countries

## Sources

- ODYSSEE database: https://www.indicators.odyssee-mure.eu/energy-efficiency-database.html
- ODYSSEE air-conditioning per dwelling indicator: https://www.odyssee-mure.eu/publications/efficiency-by-sector/households/unit-consumption-air-conditioning.html
- Natural Earth Admin 0 country boundaries: https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/
