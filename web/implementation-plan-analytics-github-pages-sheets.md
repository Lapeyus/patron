# Implementation Plan: Website Metrics on GitHub Pages + Google Sheets

## 1. Objective
Implement reliable tracking for:
- Total visitors
- Unique profile views
- Contact requests (per profile and global totals)
- Event trends over time (daily/weekly/monthly)

This plan is for implementation only. No functional code changes are included yet.

## 2. Scope
### In scope
- Frontend event instrumentation in the existing static site
- Event collection endpoint via Google Apps Script Web App
- Raw event storage in Google Sheets
- Reporting tabs and calculations in Google Sheets
- QA, rollout, and post-launch monitoring

### Out of scope (for this phase)
- Server-side user identity/auth analytics
- BI warehouse/data lake pipeline
- Advanced anti-fraud system

## 3. Constraints and Assumptions
- Site is hosted on GitHub Pages (static hosting).
- Event data is stored in Google Sheets.
- Current measured volume is still low (~68 events / 30-day month based on shared historical data), so Apps Script + Sheets is viable.
- Metrics are product/operations analytics, not legal/compliance audit logs.

## 4. Target Metrics and Definitions
- `visitor`: a browser with a persistent `visitor_id` (localStorage).
- `session`: 30-minute inactivity window; new `session_id` after timeout.
- `profile_view`: when a profile modal is opened.
- `unique_profile_view`: unique combination of (`date`, `visitor_id`, `profile_id`).
- `contact_request`: user click on contact CTA (`whatsapp`, `ask_for_contact`, `phone`).

## 5. High-Level Architecture
1. Frontend emits events from user actions.
2. Events sent to Apps Script Web App endpoint via `sendBeacon` (fallback to `fetch`).
3. Apps Script validates payload and appends rows to Google Sheet.
4. Reporting tabs aggregate raw events into business KPIs.

## 6. Event Instrumentation Plan (Frontend)
## 6.1 Event hooks
- Page load: emit `page_view`.
- Profile open: emit `profile_view`.
- Contact CTA click:
  - WhatsApp direct: `contact_request` with `contact_type=whatsapp`.
  - Ask for contact CTA: `contact_request` with `contact_type=ask_for_contact`.
  - Phone CTA click: `contact_request` with `contact_type=phone`.

## 6.2 Event payload schema
- `event_id` (UUID)
- `event_name` (`page_view`, `profile_view`, `contact_request`)
- `event_ts_utc` (ISO8601)
- `site_env` (`prod`)
- `page_path`
- `profile_id` (nullable)
- `profile_name` (nullable)
- `contact_type` (nullable)
- `visitor_id`
- `session_id`
- `lang`
- `auth_level` (if available in app state)
- `user_agent` (optional; can be omitted/minimized)
- `referrer` (optional)
- `app_version` (manual string or build date)

## 6.3 Reliability behavior
- Use in-memory queue + localStorage fallback queue.
- Flush on interval and on page hide/unload.
- Retry failed sends with backoff.
- Deduplicate with `event_id` if re-sent.

## 7. Data Collection Plan (Apps Script)
## 7.1 Web App endpoint
- `doPost(e)` receives JSON payloads.
- Validate required fields and allowed `event_name`.
- Add server timestamp.
- Use `LockService` before appending rows.
- Return JSON success/failure response.

## 7.2 Anti-abuse/basic hardening
- Strict schema validation and field length limits.
- Drop malformed events.
- Optional simple token in payload (not strong security, only noise reduction).
- Maintain denylist/rate checks in script if abuse appears.

## 7.3 Spreadsheet structure
- `raw_events` (append-only source of truth)
- `daily_overview`
- `profile_metrics`
- `contact_metrics`
- `ops_errors` (invalid payloads, script errors summary)

Suggested `raw_events` columns:
- `server_ts`, `event_ts_utc`, `event_id`, `event_name`, `profile_id`, `profile_name`, `contact_type`, `visitor_id`, `session_id`, `page_path`, `lang`, `auth_level`, `site_env`, `app_version`

## 8. Reporting Plan (Google Sheets)
## 8.1 Daily overview
- Total visitors (distinct `visitor_id` by day)
- Sessions (distinct `session_id` by day)
- Total profile views
- Unique profile views
- Total contact requests
- Contact conversion rate: `contact_requests / profile_views`

## 8.2 Profile metrics
- Per-profile views
- Per-profile unique views
- Per-profile contacts
- Per-profile contact rate

## 8.3 Contact metrics
- Contacts by type (`whatsapp`, `ask_for_contact`, `phone`)
- Daily/weekly trend charts

## 9. Privacy and Data Handling
- Do not store phone numbers, names of end users, or message contents.
- Use pseudonymous IDs (`visitor_id`, `session_id`).
- Keep only operational metadata required for reporting.
- Define retention policy (example: raw events retained 18 months).

## 10. Rollout Plan
## Phase 0: Design and setup (0.5-1 day)
- Confirm final metric definitions and dashboard layout.
- Create Google Sheet and Apps Script project.

## Phase 1: Collector implementation (1 day)
- Build `doPost` endpoint.
- Add validation, locking, and append logic.
- Deploy Web App and test with sample payloads.

## Phase 2: Frontend instrumentation (1-1.5 days)
- Add tracker utility module.
- Instrument `page_view`, `profile_view`, and contact CTA clicks.
- Implement queue/retry/sendBeacon fallback.

## Phase 3: Reporting tabs (0.5-1 day)
- Build formulas/pivots/charts in Sheets.
- Validate KPI outputs with controlled test data.

## Phase 4: QA and launch (0.5-1 day)
- Cross-browser smoke tests.
- Verify no UI regressions and acceptable performance.
- Launch with monitoring checklist.

Estimated total: **3.5 to 5.5 working days**.

## 11. QA Checklist
- Event fires exactly once for each intended action.
- No duplicate events during normal use.
- Contact click events include correct `profile_id` and `contact_type`.
- Events still send on quick navigation/close.
- Failed endpoint temporarily queues and later retries.
- Dashboard totals match sampled manual test sessions.

## 12. Risks and Mitigations
- Ad blockers may block some client-side requests.
  - Mitigation: monitor discrepancy trends, not absolute perfection.
- Apps Script quotas may become a limit if usage spikes heavily.
  - Mitigation: monitor volume and migrate collector to a lightweight API if needed.
- Google Sheet growth over time.
  - Mitigation: archive old rows periodically to a secondary sheet/file.

## 13. Acceptance Criteria
- Dashboard shows daily visitors, unique profile views, and contact requests.
- Per-profile contact counts are available and accurate against test logs.
- Data appears in Sheets within 1 minute of tracked action.
- No noticeable UX degradation on mobile/desktop.

## 14. Future Enhancements (Optional)
- Add campaign/source tagging (UTM breakdown).
- Add weekly email summary from Apps Script.
- Add anomaly alerts (sudden drop/spike in contacts).
- Migrate raw events to BigQuery if scale requires.
