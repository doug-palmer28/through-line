# Test profile: Keystone Family Housing Partners (fictional)

A reusable, fully synthetic test organization for Through Line. Use it whenever you want to run the whole app end to end with the same fake firm and the same fake data.

| File / folder | What it is |
|---|---|
| `profile.json` | The fake firm: account, documents to upload, interview answer bank, feedback to give, 24 synthetic participants (fixed demographics + seeded response pattern), program numbers, made-up **brand** (design standards, colors, fonts, tagline), and the **report** request (audience, length, notes) |
| `keystone_logo.png` | A generated, fictional logo (teal circle, house, gold keystone) |
| `../../test_organizations/05_keystone_family_housing_partners.pdf` | The document the Share step uploads |
| `demo_screens/` | Screenshots from the 2026-10-20 live run (used by the walkthrough deck) |
| `runs/20261020_104049/` | Step 15 live run: program numbers uploaded through 6 monthly templates, then the Report Designer. `funder_deck.pptx` (14 slides with speaker notes), `impact_one_pager.pdf`, `impact_report.pptx` (quick report in the Keystone brand), `report_draft.json` (draft + privacy report), `program_numbers_2026-09.xlsx` (a filled template), and `preview_*.png` |
| `runs/2026-10-20_live_demo/` | The first live run: `studio.json` (full interview transcript, logic model, plan, cited sources), `run_log_tools_collect.json` (Survey Review Bot result + fixes applied), `participant_codes.json`, `dashboard.json`, `survey_data.xlsx`, `impact_report.pptx`, and `Through_Line_live_walkthrough.pptx` |

## Run it again

From the `Final Project` folder, with the backend running:

```
.venv/Scripts/python scripts/run_test_profile.py data/test_profiles/keystone_family_housing
```

- `--from tools | collect | numbers | export | report` resumes part-way (it signs in as the profile's account first). `--from report` just rebuilds the funder deck and flyer.
- `numbers` enters program numbers the way staff would: download each month's Excel template, fill it in, upload it.
- The Studio, Survey Review Bot, and Report Designer stages make **live gpt-6-luna calls**. Only run them when Doug asks.
- Since Step 15b each organization gets **one** report design. To rebuild Keystone's report, first run `.venv/Scripts/python scripts/operator_tools.py allow 1 report` (Keystone is org 1 in the real database).
- `--runs-dir <folder>` writes the run somewhere else (e.g. a scratch folder for rehearsals against `tests/demo_server.py`).
- Each run writes a new `runs/<timestamp>/` folder. The same seed gives the same participant data.
- If the account already exists (e.g. on the real database), the script signs in instead of signing up.

## Rebuild the walkthrough deck

```
.venv/Scripts/python scripts/build_demo_deck.py data/test_profiles/keystone_family_housing 2026-10-20_live_demo
```

Test-only credentials: `keystone.test` / see `profile.json`. Everything here is synthetic.
