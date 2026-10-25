# Evidence

Proof behind each claim in the report, in one place. Everything here is real output from the app, its tests, or the live site. Nothing is a mock-up.

| Claim | Evidence |
|---|---|
| **It works end to end, on the real model** | [`examples/keystone/`](../examples/keystone/): every file the app produced for Keystone (logic model, survey, data, funder deck, flyer, grant draft). [`studio.json`](../data/test_profiles/keystone_family_housing/runs/2026-10-20_live_demo/studio.json) is that live gpt-6-luna run's record: the five interview questions and answers, the logic model, the measurement plan, every cited source, and the token count. |
| **Token counts are measured, not estimated** | [`live_token_usage_2026-10-24.json`](live_token_usage_2026-10-24.json): the live site's token ledger by organization and task, including cached input and web searches. The app's own AI usage page is pictured in the report (Tokenomics). |
| **A real user tried it** | Jodi Walker, executive director of Kids at Their Best, completed the Logic Model Studio on the live site: 26 agent runs, 285,623 input tokens (30% cached), 30,202 output (in the ledger above). Her debrief is in the report's Impact section. Two more outside testers used it on their own: Sara S. set up a food bank (Studio finished, a survey built and reviewed, three program numbers; 25 runs, 35% of input cached), and Sara B. built a sewing cooperative's logic model on her phone (24 runs, 32% cached). |
| **Agents can't be steered by hidden text** | [`hidden_text_defense.md`](hidden_text_defense.md): the same booby-trapped PDF, Word, PowerPoint, and web page read by a standard reader (26 hidden instructions get through) and by Through Line (0 get through, all visible text kept). |
| **Usage limits actually stop runs** | [`audit_log_check.md`](audit_log_check.md): `limit_reached` entries from real runs, where the per-run consult budget refused extra agent calls. The allowance tests are in `tests/test_limits_grants.py`. |
| **The audit log can't be quietly edited** | [`audit_log_check.md`](audit_log_check.md): 456 hash-chained entries, chain intact, with counts of every event type. |
| **The code is tested** | [`test_results.txt`](test_results.txt): all 64 offline tests passing, by name. They cover org isolation, sign-in, uploads that are never saved, privacy scrubbing, hidden text, usage limits, the view-only demo, zip bombs, and more. |
| **It was reviewed for security** | [`output/harness.md` §10i](../output/harness.md): two independent code reviews (before launch and before submission) and what was fixed from each. |

## Rebuild

```bash
.venv/Scripts/python scripts/build_evidence.py     # test results, hidden-text comparison, audit-log check (offline)
.venv/Scripts/python scripts/build_examples.py     # examples/keystone/ (no AI calls)
```

The live token ledger comes from the Render Shell: `python ../scripts/operator_tools.py report-data`.
