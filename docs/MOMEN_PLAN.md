# Momen integration plan: technician work-order app

Status: **planned, nothing built yet.** Momen is optional for GenHacks. The sponsor gives every participant $100 in credit (code valid Nov 1 – Dec 25; redeem link and access code are in the GenHacks Devpost update “Momen Workshop for GenHacks”) and runs a workshop with Momen's CEO on **Nov 20, 4:30–5:30 PM PST**. Using Momen gives no stated judging bonus. We use it because it adds a real step to the product.

## 1. Why Momen, and what it adds

Today Pump Detective stops at a recommendation: “PLANNED · clean the strainer by 7 Dec”. Real predictive maintenance closes the loop:

```
Sensors (synthetic) → Physics + forecast (Python) → Work order (rules / AI)
        ↑                                                  ↓
   Re-run forecast  ←  Verified result  ←  Technician completes it in Momen
```

Momen becomes the **technician side**: a small app with a database of work orders. A technician opens it, sees what to do and by when, marks the job done and records the strainer Δp after cleaning. Pump Detective reads the result back and shows whether cleaning worked.

**Why not rebuild Pump Detective in Momen?** The physics, the forecast and the tests are the strongest parts, and they belong in Python. Momen is used where no-code is strong: data entry, lists, status workflow and a mobile-friendly UI.

## 2. Architecture

| Part | Built with | Job |
|---|---|---|
| Pump Detective | Python / Streamlit (existing) | Forecast, findings, work-order text, **Send to Momen** button, status panel |
| `momen_client.py` | Python stdlib `urllib` (new) | Two calls to Momen's GraphQL API: create a work order, list work orders |
| Momen project | Momen no-code | `work_order` table, list page, detail page with “Mark done” |

How they talk (verified against Momen's [Runtime API reference](https://docs.momen.app/docs/code/runtime_api/)):

- Each Momen project has one GraphQL endpoint: `https://villa.momen.app/zero/{projectExId}/api/graphql-v2`.
- Momen generates operations for each table. For `work_order`, that means `insert_work_order_one` (create), `work_order` (list, with `where` / `order_by`) and `update_work_order_by_pk`.
- A server-side script authenticates with the project's **Admin Bearer Token** (`Authorization: Bearer …`), found under **Developer access** in the Momen editor.
- **Security:** the token stays on the Streamlit server, in `.streamlit/secrets.toml` locally (already in `.gitignore`) and in the host's secrets settings when deployed. It must never go into the repo, the page, or the demo video.

Example create call (field names must match what you create in Momen):

```graphql
mutation CreateWorkOrder($object: work_order_insert_input!) {
  insert_work_order_one(object: $object) { id }
}
```

## 3. Momen data model (build this exactly; the names become the API)

Table **`work_order`** (Momen adds `id` and `created_at` automatically):

| Field | Type | Example | Filled by |
|---|---|---|---|
| `asset` | Text | CHWPP-01 suction strainer | Pump Detective |
| `action` | Text | Schedule suction strainer cleaning and inspection | Pump Detective |
| `priority` | Text | URGENT / HIGH / PLANNED / NONE | Pump Detective |
| `complete_by` | Text (YYYY-MM-DD) | 2026-12-07 | Pump Detective |
| `driver` | Text | NPSH WARNING (margin 1.00 m lost) | Pump Detective |
| `evidence` | Text (long) | Δp* 10.7 kPa vs 5 kPa clean, +1.18 %/day … | Pump Detective |
| `dp_before_kpa` | Decimal | 10.7 | Pump Detective |
| `forecast_scenario` | Text | Gradual fouling (synthetic) | Pump Detective |
| `status` | Text | OPEN → IN_PROGRESS → DONE | Technician |
| `dp_after_kpa` | Decimal | 5.3 | Technician |
| `technician_notes` | Text (long) | Heavy debris in basket, flushed | Technician |
| `completed_at` | Date/time | — | Technician (“Mark done”) |

`complete_by` is Text on purpose: it avoids date-format surprises in the first version.

## 4. Momen pages

1. **Work orders (list).** Cards sorted by priority, then `complete_by`, with a status filter. Colour the priority: URGENT red, HIGH orange, PLANNED yellow.
2. **Work order (detail).** Shows all fields read-only, plus inputs for `dp_after_kpa` and `technician_notes`. Buttons:
   - **Start**: status → IN_PROGRESS.
   - **Mark done**: status → DONE and `completed_at` → now.

Optional, only if time remains: a Momen AI Agent that answers technician questions about one work order. Not recommended at first, because it duplicates the AI that already lives in Pump Detective.

## 5. Pump Detective changes (Python, done with Claude)

- **New file `momen_client.py`:**
  - `create_work_order(fields) -> id`
  - `list_work_orders(limit=20) -> rows`
  - Includes timeouts and clear error messages, never sends the token anywhere but Momen, and treats GraphQL `errors` as failures.
- **Detective Intelligence:** a **Send work order to Momen** button under the maintenance recommendation. It sends the rule-based work order fields, not free AI text, so the record is always consistent. It shows the new work-order id, and refuses to send if the priority is NONE.
- **Work-order status panel:** lists recent work orders from Momen. For DONE orders it compares `dp_after_kpa` with the 5 kPa clean reference: “Verified: back to clean” or “Still restricted: inspect again”.
- **Feature flag:** without `MOMEN_GRAPHQL_URL` and `MOMEN_ADMIN_TOKEN` configured, the button explains how to connect Momen and the rest of the app works unchanged. A **Download work order (JSON)** fallback allows manual entry.
- **Tests:** unit tests with a mocked HTTP response for both calls, including an error response.

## 6. Step-by-step schedule

| # | Step | Who | Estimate | Done when |
|---|---|---|---|---|
| 0 | Redeem the $100 credit; create a Momen project; attend or watch the Nov 20 workshop | You | 1 h + workshop | Empty project opens in the editor |
| 1 | Create the `work_order` table exactly as in section 3; publish | You (Claude can guide live) | 1 h | Table visible in GraphiQL (Developer access) |
| 2 | In GraphiQL, insert one test row with `insert_work_order_one` | You + Claude | 20 min | Row appears in Momen's data view |
| 3 | Put the endpoint and admin token in `.streamlit/secrets.toml` (local only) | You | 5 min | File exists and is git-ignored |
| 4 | Build `momen_client.py`, the button, the status panel and tests | Claude | 1–2 h | Send from Pump Detective → row appears in Momen |
| 5 | Build the Momen list and detail pages with Start / Mark done | You | 2–3 h | Technician can complete an order on a phone |
| 6 | End-to-end check: send → complete in Momen → verified in Pump Detective | Both | 30 min | Status panel shows “Verified: back to clean” |
| 7 | Update README, DEMO script (≈20 s for the loop) and Devpost tools list | Claude | 30 min | Docs mention Momen and the loop |

Total: about 6–8 hours, mostly learning Momen. Deadline: Devpost closes **Dec 26, 12:00 AM ET**, and the Momen credit code expires **Dec 25**.

## 7. Risks and decisions

- **The admin token is powerful.** Keep it server-side only. If it leaks (repo, screenshot, video), regenerate it in Momen right away. A later improvement would be a dedicated Momen Actionflow with limited permissions instead of the admin token.
- **Field names must match exactly** between Momen and `momen_client.py`. Section 3 is the contract, so change both together.
- **Momen plan limits** (records, publishing) are unknown until the project is created. Check them in step 0.
- **Deployment:** if Pump Detective is deployed, the token goes into the host's secret settings, never into the code.
- **Scope guard:** if Momen eats too much time, stop after step 4 with the GraphQL push working. The data model plus Momen's built-in data view is already demonstrable.

## 8. Demo addition (≈20 seconds)

“Pump Detective sends the work order to our Momen technician app. The technician cleans the strainer, records 5.3 kPa and marks it done, and Pump Detective confirms the strainer is back to its clean reference. That closes the predict → act → verify loop.”
