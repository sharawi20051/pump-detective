# Momen integration plan: GO SMALL

**Decision:** build a small closed loop. Pump Detective sends a work order → the technician completes it in Momen with a post-cleaning reading → Pump Detective reads it back and **verifies** the result.

**Status:**
- Step 1, verification in Python, is **done**: `verification.py` plus the “Verify the maintenance” form in the Fouling forecast tab.
- Steps 2–7 are not started.

Momen is optional for GenHacks. The sponsor gives every participant $100 in credit (code valid Nov 1 – Dec 25; redeem link and access code are in the GenHacks Devpost update “Momen Workshop for GenHacks”) and runs a workshop on **Nov 20, 4:30–5:30 PM PST**. Using Momen gives no stated judging bonus.

## Why, and the boundary

- **Value split:** the value is in verification, which lives in Python. Momen supplies what Streamlit cannot do well: persistent shared work orders and a separate, phone-friendly technician app with its own login.
- **Calculations stay in Python.** Momen stores and displays work orders only. All engineering stays in Pump Detective (normalisation, uncertainty, verdicts, NPSH).
- **Pump Detective must work without Momen.** With no Momen configuration, the Send button is hidden and the manual verification form still works.

```
Forecast → Work order ──(send)──▶ Momen: technician enters Δp + flow, taps Done
   ▲                                              │
   └──── Verify (flow-normalised Δp*, k=2 band, NPSH) ◀──(read back)──┘
```

## Minimum schema: table `work_order`

Momen adds `id` and `created_at` itself.

| Field | Type | Written by |
|---|---|---|
| `action` | Text | Pump Detective |
| `priority` | Text: URGENT / HIGH / PLANNED | Pump Detective |
| `complete_by` | Text, YYYY-MM-DD | Pump Detective |
| `dp_star_before_kpa` | Decimal | Pump Detective |
| `status` | Text: OPEN / DONE | Pump Detective (OPEN), technician (DONE) |
| `dp_after_kpa` | Decimal | Technician |
| `flow_after_lps` | Decimal | Technician. Required, because verification normalises Δp by flow². |

## Verification rules (already implemented in `verification.py`)

- **Normalise for flow:** Δp* = Δp·(Q_ref/Q)². Readings below 30 % of design flow are rejected.
- **Uncertainty:**
  - Instrument accuracies come from datasheets and are treated as rectangular (GUM); a single DP transmitter and two absolute transmitters are handled differently.
  - The baseline carries the same instrument uncertainty plus an optional repeatability term.
  - The result is an expanded uncertainty U at **k = 2** (≈95 %).
- **Verdicts:**
  - **RESTORED:** within the baseline ± U.
  - **IMPROVED, NOT CLEAN:** above the band but below the maintenance limit.
  - **NOT EFFECTIVE:** at or above the limit.
  - **SUSPICIOUSLY LOW:** below the band; possible torn screen, bypass or sensor fault.
- **NPSH outcome:** reported separately at design flow, together with the “suction still below atmospheric” note when it applies.
- **Defaults are example values, not field data:** the datasheet figures (0–400 kPa transmitters at ±0.1 % of span, flow meter at ±0.5 %) and the 5 kPa baseline.

## Security

| Item | Rule |
|---|---|
| Momen credentials | Prefer a **dedicated Momen user** for Pump Detective with permission to create and read work orders only, signing in with username and password to get a JWT. The **Admin Bearer Token** (full data access) is acceptable only for local development. |
| Storage | `.streamlit/secrets.toml` locally (git-ignored), or the host's secrets settings when deployed. Never in code, README, issues or `.env` committed to git (add `.env` to `.gitignore` if one is ever used). |
| Who calls Momen | Streamlit's server-side Python only. Nothing is sent to the browser. Show only our own error messages, never raw exceptions, request headers or responses. |
| Technician app | Momen pages run as **guest** unless people sign in. Guests must have **no** write permission on `work_order`. The technician signs in and may only update `status`, `dp_after_kpa` and `flow_after_lps`. |
| Leaks | If a token leaks, rotate it or change the service user's password. **Admin-token rotation in Momen is not yet verified**; check it in step 2. |
| Never in GitHub or the video | The admin token, JWTs, the service user's password, `secrets.toml`, Momen's Developer-access / Connect Backend screens, and the GenHacks credit access code. |

## Tools: the Momen MCP server

The official `momen-mcp` package (v2.8.4, Nov 11 2026; README read, not yet tested) can, after **your** browser OAuth login:
- create and edit tables and permissions;
- store secrets and edit Actionflows;
- publish the backend (`sync_backend`);
- run GraphQL queries and inserts.

Page editing exists but is low-level, so build the two technician screens in Momen's visual editor (or with its AI Copilot). Installing the package runs Momen's npm code on your machine, so it needs your approval. Claude never needs to see a token.

## Implementation order

| # | Step | Who | Done when |
|---|---|---|---|
| 1 | ✅ Verification engine and manual form | Claude | Done: 25 unit tests pass |
| 2 | Redeem credit, create the Momen project, decide on `momen-mcp` (install + sign in if yes); check whether admin tokens can be rotated | You | Empty project exists |
| 3 | Create the `work_order` table (7 fields), service-user and technician roles with the permissions above; publish; insert one test row | Claude via MCP, or you with guidance | Test row visible via GraphQL |
| 4 | Put the endpoint and credentials in `.streamlit/secrets.toml` | You | File exists and is git-ignored |
| 5 | `momen_client.py` (create and list work orders, timeouts, safe errors), **Send work order** button, read back DONE orders into `verify_cleaning`; feature flag; mocked tests | Claude | Send → row appears in Momen; DONE row → verdict in Pump Detective |
| 6 | Technician screens: open-orders list + detail form (Δp, flow, Done) | You in the Momen editor, with guidance | Completed on a phone |
| 7 | End-to-end run; README, DEMO (≈25 s segment) and Devpost tools list; commit | Both | Loop works twice in a row |

**Time limit:** if step 5 doesn't work end-to-end by **Dec 15**, ship without Momen. Step 1 already tells the verification story. Devpost closes **Dec 26, 12:00 AM ET**; the credit code expires **Dec 25**.

## Video segment (≈25 s, only if it works reliably)

1. **(4 s)** Click **Send work order to Momen**.
2. **(10 s)** On a phone in the Momen app: the PLANNED order, due 7 Dec. The technician enters 5.1 kPa at 21.0 L/s and taps **Done**.
3. **(11 s)** In Pump Detective: “Strainer RESTORED: 5.20 kPa within 5.00 ± 0.94 kPa; NPSH SAFE; suction still below atmospheric, so check fill pressure.”
