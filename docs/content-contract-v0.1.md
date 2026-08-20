# Carbon Website Factory content contract V0.1

The collector may send a JSON list or `{ "items": [...] }`. The normalizer emits
a versioned feed containing task metadata and canonical content items.

Required collector fields: `id`, `country`, `city_region`, `category`,
`direction`, `title_zh`, `summary_zh`, `source_platform`, `source_url`,
`published_at`, and `verification_status`.

Optional input fields:

- `section` / `content_type`: `property` or `cooperation`; inferred when absent.
- `confidence`: number from 0 to 1. If absent, A defaults to 0.9 and B to 0.65.
- `score`: A or B; inferred from confidence when absent.
- `collected_at`: ISO-8601 timestamp with timezone; defaults to normalization time.
- `publish_status`: `hidden` or `published`; defaults to `hidden` as the human gate.

The normalizer adds `classification`, `source`, `fingerprint`, and a top-level
`task`. It removes common tracking parameters before duplicate detection. Exact
ID duplicates and normalized title/location/category duplicates are rejected.
It never commits, pushes, deploys, spends money, or contacts a source.
