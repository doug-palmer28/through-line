# Everything Through Line made for Keystone

**Keystone Family Housing Partners** is a fictional rapid-rehousing nonprofit in New Haven. All of its data is synthetic. We ran it live on gpt-6-luna on October 20, 2026, from sign-up to grant draft, and this folder holds every file the app produced for it. The final report walks through that run step by step.

Click any **PDF** to view it in your browser. The PowerPoint, Word, and Excel files are the originals a nonprofit would download: click one, then **Download** (the ⤓ button).

| Step | What it is | Made by | View | Original |
|---|---|---|---|---|
| 1. Logic model and metrics | Keystone's approved logic model (theory of change, inputs, activities, outputs, outcomes) and its measurement plan: 5 metrics with verified sources | Logic Model Studio: Team Lead, Sector Expert, Client Advocate, Evaluation Specialist, Funder Researcher | [PDF](1_logic_model_and_metrics.pdf) | [PowerPoint](1_logic_model_and_metrics.pptx) |
| 2. Survey | The participant survey built from the approved metrics and checked by the Survey Review Bot | Survey Tools + Survey Review Bot | [Survey](2_survey_1.md) | |
| 2. Program numbers | The Excel template staff use to upload monthly program numbers | Survey Tools (no AI) | | [Excel](2_program_numbers_template.xlsx) |
| 3. Dashboard data | All of Keystone's survey and program data behind the dashboard: 24 participants, 44 responses, 66 monthly values | Dashboard (no AI) | | [Excel](3_dashboard_all_data.xlsx) |
| 3. Quick report | The dashboard's one-click PowerPoint report, in Keystone's brand | Dashboard (no AI) | [PDF](3_dashboard_quick_report.pdf) | [PowerPoint](3_dashboard_quick_report.pptx) |
| 4. Funder deck | A 14-slide funder presentation with speaker notes and native, editable charts; every number is live | Report Designer + Privacy Reviewer | [PDF](4_funder_deck.pdf) | [PowerPoint](4_funder_deck.pptx) |
| 4. One-page flyer | The matching one-page flyer | Report Designer + Privacy Reviewer | [PDF](4_one_page_flyer.pdf) | |
| 5. Grant draft | A tailored application to the El Pomar Foundation, with yellow `[ADD: …]` placeholders where facts were missing and an honest eligibility flag | Funder Researcher + Grant Writer + Privacy Reviewer | [PDF](5_grant_application_draft.pdf) | [Word](5_grant_application_draft.docx) |

**To see these inside the app**, sign in to the live site with the Keystone demo login (it's in the submitted report and slides).

**How this folder was made:** `python scripts/build_examples.py` loads Keystone's saved package into a throwaway database and downloads each file through the app, with no new AI calls. The files are the same ones the app gives a nonprofit. The PDF copies were made with Microsoft Office.
