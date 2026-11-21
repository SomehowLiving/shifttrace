# Invalid runs (kept for the record, excluded from Agent quality)

- `20261121-113143` (vision_dataset): the console's built-in test feed (on by default for a tab that joins a session)
  replaced the harness's injected camera, so the agent saw the test-feed C-204 panel for every dataset photo and
  described a "KS-75 compressor at 108 C" each time. Harness bug, not a model result. Fixed in scripts/scenarios.py
  (failure #42); the run was repeated.
