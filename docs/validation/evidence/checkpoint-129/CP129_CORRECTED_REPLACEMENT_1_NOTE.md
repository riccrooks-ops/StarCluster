# CP129 Corrected Replacement 1

The original CP129 candidate failed its first native Windows RepositoryOnly run at stage 9 after all earlier gates passed. The complete one-trial smoke reached evidence serialization and raised:

`ValueError: dict contains fields not in fieldnames: 'changed_fields'`

Root cause: `smoke_lane_summary.csv` inferred field names from the first baseline row (`lane`, `variants`, `trial_errors`, `elapsed_seconds`), while holdback rows later added `changed_fields`. Corrected Replacement 1:

- gives every smoke lane row `changed_fields` with baseline value 0;
- writes the summary with an explicit five-column schema;
- adds a permanent regression that serializes baseline and holdback rows through the actual CSV writer;
- exposes wrapper `-Jobs` as a validated 1-61 performance parameter, default 24;
- raises expected Python tests from 176 to 177.

No production C#, technology value, scenario definition, study population, seed, trial count, pairing identity, or substantive workload changes. CP128 remains the accepted baseline until this replacement passes native Windows acceptance.
