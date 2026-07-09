# Telemetry Dashboard - rb_telemetria

This file (`telemetry_grafana.json`) defines a Grafana dashboard (`dashboard.grafana.app/v2` format) responsible for displaying real-time telemetry data from the project's autonomous forklift. It can be imported directly into Grafana to recreate the monitoring panel.

## Overview

- **Dashboard Title:** `rb_telemetria`
- **Data Source:** PostgreSQL/TimescaleDB (datasource `efr0zsd6jbvnke`), dataset `projeto_b`
- **Queried Table:** `rb_emp`
- **Default Time Range:** Last 5 minutes (`now-5m` to `now`)
- **Available Auto-refresh:** 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 1d (no fixed interval is applied by default)
- **Timezone:** Browser's timezone

## Panels

| Panel | Title | Type | Source Column | Calculation/Query | Range (min-max) |
|---|---|---|---|---|---|
| panel-1 | Voltage | gauge | `tensao_v` | Average per 1s bucket | 11 to 12.4 |
| panel-2 | Current | gauge | `corrente_ma` | Average per 1s bucket | 0 to 3 |
| panel-3 | Power | gauge | `potencia_mw` | Average per 1s bucket | 0 to 37.2 |
| panel-4 | Left RPM | gauge | `rpm_esq` | Average per 1s bucket | 0 to 150 |
| panel-5 | Right RPM | gauge | `rpm_dir` | Average per 1s bucket | 0 to 150 |
| panel-6 | Mode | stat | `tipo` | Latest reading (`ORDER BY created_at DESC LIMIT 1`) | - |
| panel-7 | Stepper Motor Failure? | stat | `falha_motor_passo` | Latest reading (`ORDER BY created_at DESC LIMIT 1`) | - |

### Panels 1 to 5 (Time Series Gauges)

These panels use TimescaleDB's `time_bucket('1 second', created_at)` to aggregate data into 1-second windows and calculate the average (`AVG`) of the corresponding column within the time range selected on the dashboard (`$__timeFilter(created_at)`). All of them display a sparkline and use a continuous color gradient (green to red), except Current and Right RPM, which use percentage-based thresholds (60% yellow, 80% red).

### Panel 6 - Mode

Displays the system's current operation mode, translating the numerical value from the `tipo` column into a textual label:

- `0` -> Manual
- `1` -> Autonomous
- `2` -> Search
- `3` -> Fork
- Any other value -> Unknown

### Panel 7 - Stepper Motor Failure?

Displays the latest status from the `falha_motor_passo` column, translated into text:

- `0` -> No
- `1` -> Yes
- Any other value -> Unknown

## Screen Layout

The panels are organized in a 22-column grid, across three rows:

1. **Row 1** (height 6): Voltage, Current, and Power side by side.
2. **Row 2** (height 6): Stepper Motor Failure, Left RPM, and Right RPM side by side.
3. **Row 3** (height 4): Mode, taking up the full width (22 columns).

## Reusability Requirements

For this dashboard to work in another environment, the following is required:

1. A Grafana instance (Cloud or self-hosted) compatible with the `dashboard.grafana.app/v2` schema.
2. A configured `grafana-postgresql-datasource` pointing to the PostgreSQL/TimescaleDB database that contains the `projeto_b` dataset and the `rb_emp` table.
3. Update the `datasource.name` field in each panel (`efr0zsd6jbvnke`) to match the UID of the datasource configured in the new environment, if different.
4. Ensure the `rb_emp` table has at least the following columns: `created_at`, `tensao_v`, `corrente_ma`, `potencia_mw`, `rpm_esq`, `rpm_dir`, `tipo`, and `falha_motor_passo`.

## Importing into Grafana

1. In Grafana, go to **Dashboards > New > Import**.
2. Paste the contents of `telemetry_grafana.json` or upload the file.
3. Select or adjust the corresponding PostgreSQL datasource.
4. Confirm the import.
