# OpenCEM Dataset

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Data format](https://img.shields.io/badge/Data-CSV-blue.svg)](data)
[![Project](https://img.shields.io/badge/Project-OpenCEM-0f766e.svg)](https://tongxin.me/opencem/)

Real-world microgrid measurements and natural-language context records for
context-aware energy management research.

OpenCEM, short for Open In-Context Energy Management, is an open-source digital
twin ecosystem for studying renewable energy systems whose behavior is shaped
not only by electrical signals, but also by human schedules, compute workloads,
system events, weather, and other contextual information. This repository hosts
the public dataset used by the OpenCEM platform.

The data is collected from an on-campus PV-and-battery microgrid at
CUHK-Shenzhen. It includes high-frequency inverter measurements, battery state,
PV generation, grid import, load demand, thermal readings, and timestamped
natural-language context records.

## Dataset Snapshot

The numbers below are derived from the CSV files currently checked into this
repository.

| Metric | Value |
| --- | --- |
| Measurement rows | 1,798,079 |
| Context records | 14,995 |
| Measurement coverage | 2025-07-14 05:53:32 UTC to 2026-04-03 04:01:22 UTC |
| Context coverage | 2024-07-27 10:00:00 UTC to 2026-01-11 06:28:04 UTC |
| Measurement days | 230 unique UTC dates |
| Context days | 74 unique UTC dates |
| Measurement interval | Median 13 seconds per inverter |
| Inverters | 2 |
| Measurement columns | 82 |
| Repository data size | About 418 MB |

## Repository Layout

```text
.
|-- api/v1/meta/index.json      # Static metadata index for public API access
|-- data/
|   |-- measurements/           # Half-month CSV partitions of analog measurements
|   `-- context/                # CSV partitions of context records
|-- scripts/ingest.py           # SQLite-to-CSV export helper
|-- LICENSE
`-- README.md
```

Measurement files use the pattern `YYYY-MM-a.csv` for days 1-15 and
`YYYY-MM-b.csv` for days 16 through the end of the month. Context files use the
same convention when records exist for a partition; `data/context/other.csv`
contains records outside the regular monthly partition range.

## Physical System

The OpenCEM dataset comes from a real campus microgrid with two independent
PV-battery subsystems. The installation includes:

| Component | Description |
| --- | --- |
| Solar PV | 2 arrays, 26 monocrystalline panels per array, 480 W per panel |
| Battery storage | 200 Ah lithium-ion batteries at 51.2 V nominal |
| Inverters | SPI4880V150-500P hybrid inverters, 8 kW rated output |
| Loads | Research workstations and HVAC equipment |
| Data bridge | Modbus/RS485 inverter measurements exported to the dataset |

This combination makes the dataset useful for studying forecasting, scheduling,
MPC, reinforcement learning, anomaly analysis, and language-conditioned energy
management.

## Data Schema

### Measurements

Measurement rows are stored in `data/measurements/*.csv`. Each row is one
timestamped inverter reading.

Common columns include:

| Column | Meaning |
| --- | --- |
| `read_ts` | Unix timestamp of the measurement |
| `inverter` | Inverter ID |
| `battvolt`, `battcurr`, `battsoc` | Battery voltage, current, and state of charge |
| `pv1volt`, `pv1curr`, `pv1power` | PV array voltage, current, and power |
| `outw_a`, `outsumw`, `outsumva` | Output active/apparent power readings |
| `linevolta`, `linefreq` | Grid voltage and frequency |
| `gridpowerw_a`, `gridcurr_a` | Grid import power/current |
| `temper1` through `temper4` | Temperature sensor readings |

The full 82-column schema is available in the CSV header and in
`api/v1/meta/index.json`.

### Context

Context records are stored in `data/context/*.csv`.

| Column | Meaning |
| --- | --- |
| `id` | Context record ID |
| `recorded` | Unix timestamp when the context was recorded |
| `start` | Unix timestamp when the context starts applying |
| `end` | Unix timestamp when the context stops applying |
| `value` | JSON payload containing source, description, and optional metadata |

The `value` field typically includes `source` and `textual_description`. Sources
include manual annotations and workstation logs.

Example context payload:

```json
{
  "inverter": 1,
  "source": "workstation2_log",
  "device": "workstation2",
  "task_type": "CNN fitting, GPU load",
  "textual_description": "The model vgg13 is fitted on CIFAR10 using sgd for 2 epochs with bs=128."
}
```

## Accessing the Data

You can use the CSV files directly from this repository or fetch them from the
public raw GitHub URLs.

```python
import pandas as pd

base = "https://raw.githubusercontent.com/OpenCEM-platform/opencem-dataset/main/data"

measurements = pd.read_csv(f"{base}/measurements/2025-12-b.csv")
context = pd.read_csv(f"{base}/context/2025-12-b.csv")

print(measurements.head())
print(context.head())
```

Metadata is served as a static JSON file:

```python
import requests

meta_url = "https://opencem-platform.github.io/opencem-dataset/api/v1/meta/index.json"
meta = requests.get(meta_url, timeout=30).json()

print(meta["name"])
print(meta["stats"])
```

For shell-based workflows:

```bash
curl -L -O https://raw.githubusercontent.com/OpenCEM-platform/opencem-dataset/main/data/measurements/2025-12-b.csv
curl -L -O https://raw.githubusercontent.com/OpenCEM-platform/opencem-dataset/main/data/context/2025-12-b.csv
```

## Updating Dataset Exports

The ingestion script exports new records from a local SQLite database into the
partitioned CSV layout used by this repository.

```bash
python scripts/ingest.py --db /path/to/opencem_dataset.db
```

Use `--full` to regenerate all CSV partitions from the database:

```bash
python scripts/ingest.py --db /path/to/opencem_dataset.db --full
```

After exporting, review the changed files, then commit the updated data and
metadata.

## Related Resources

- Project website: <https://tongxin.me/opencem/>
- Dataset explorer: <https://tongxin.me/opencem/dataset.html>
- API and simulator docs: <https://tongxin.me/opencem/api.html>
- Simulator repository: <https://github.com/OpenCEM-platform/opencem_simulator>
- Metadata endpoint: <https://opencem-platform.github.io/opencem-dataset/api/v1/meta/index.json>
- Paper: <https://arxiv.org/abs/2604.05429>

## Citation

If you use OpenCEM in academic work, please cite:

```text
T. S. Bartels, R. Wu, X. Lu, Y. Lu, F. Xia, H. Yang, Y. Chen, and T. Li.
"Bridging Natural Language and Microgrid Dynamics: A Context-Aware Simulator
and Dataset." arXiv:2604.05429, 2026.
```

## License

This repository includes an MIT license. The dataset metadata also identifies
the data license as CC BY 4.0. Please preserve attribution and cite the OpenCEM
paper when using or redistributing the dataset.
