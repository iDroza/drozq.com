"""Build /fello/ : Joshua's internal reference for the Fello API (noindex).

Scaffolded from short-sale/index.html (Variant B fixed-header chrome, the
Panda patch, the funnel markers, the footer, the mobile-nav script, and a
sell-mode closing pill). This script replaces:

  - <title> / meta description / canonical / og:* / twitter:*
  - inserts <meta name="robots" content="noindex,follow"> (internal page:
    never in the sitemap, never in the header nav, never in llms.txt)
  - the <style id="drozq-page-chrome"> block
  - everything between <main ...> and </main>
  - strips the short-sale-only <style id="shs-css"> block

Content source of truth: notes/fello/fello-api-brief.md (researched
2026-09-02 against docs.fello.ai + the help center + a live key probe).
Update the brief and this script together. The page carries NO credentials;
those live in the gitignored scripts/.fello_secret and, once wired, in
Cloudflare env vars (FELLO_API_KEY / FELLO_CLIENT_SECRET).

Run:  python scripts/build_fello.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "short-sale" / "index.html"
TARGET = ROOT / "fello" / "index.html"

TITLE = "Fello API capabilities | drozq.com internal"
DESCRIPTION = (
    "Internal reference: every record the Fello API can read or write, every "
    "webhook it pushes, the rate limits, and what gets built on drozq.com with it."
)
CANONICAL = "https://drozq.com/fello/"
OG_TITLE = "Fello API capabilities"
OG_DESCRIPTION = DESCRIPTION

PROBE_DATE = "September 2, 2026"

# ---------------------------------------------------------------------------
# Page chrome: Variant B fixed header + warm masthead + every .fl-* style the
# page uses (scoped, so nothing rides on an uncompiled Panda utility).
CHROME = (
    '<style id="drozq-page-chrome">'
    '@layer base{#__next>header{position:fixed !important;top:0;left:0;right:0}}'
    '#__next>header{box-shadow:0 1px 5px rgba(0,0,0,.11)}'
    'body{padding-top:48px}@media(min-width:768px){body{padding-top:64px}}'
    'section[aria-labelledby=fello-hero-title]{background:#f2f0ef;padding-top:56px;padding-bottom:40px}'
    '@media(min-width:768px){section[aria-labelledby=fello-hero-title]{padding-top:84px;padding-bottom:56px}}'
    '[id]{scroll-margin-top:80px}'
    '.fl-wrap{max-width:1035px;margin:0 auto;padding:0 32px;box-sizing:border-box}'
    '@media(min-width:1024px){.fl-wrap{padding:0 16px}}'
    '.fl-head{max-width:720px;margin:0 auto 28px;text-align:center}'
    '.fl-head h2{font-weight:800;opacity:.87;color:#2b2b2b;font-size:26px;line-height:34px;letter-spacing:.3px;margin:0 0 10px}'
    '.fl-head p{color:#3f4650;font-size:16px;line-height:26px;margin:0}'
    '@media(min-width:768px){.fl-head h2{font-size:32px;line-height:40px}}'
    '.fl-stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:1035px;margin:0 auto}'
    '.fl-stat{background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:20px 16px;text-align:center}'
    '.fl-stat b{display:block;color:#1a1816;font-size:28px;line-height:32px;font-weight:800;letter-spacing:.3px}'
    '.fl-stat span{display:block;color:#d92228;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-top:8px}'
    '@media(min-width:768px){.fl-stats{grid-template-columns:repeat(4,1fr);gap:20px}.fl-stat b{font-size:36px;line-height:40px}}'
    '.fl-note{max-width:720px;margin:20px auto 0;text-align:center;color:#3f4650;font-size:14px;line-height:22px}'
    '.fl-note code,.fl-inline{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;background:#f2f0ef;border:1px solid #e5e5e5;border-radius:6px;padding:1px 6px;color:#1a1816}'
    '.fl-grid{display:grid;grid-template-columns:1fr;gap:16px}'
    '@media(min-width:768px){.fl-grid--2{grid-template-columns:1fr 1fr;gap:20px}.fl-grid--3{grid-template-columns:1fr 1fr 1fr;gap:20px}}'
    '.fl-card{background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:24px;box-sizing:border-box}'
    '.fl-card--warm{background:#fbf8f4;border-color:#ece8e2}'
    '.fl-eyebrow{color:#d92228;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 8px}'
    '.fl-card h3{color:#1a1816;font-size:19px;line-height:26px;font-weight:700;margin:0 0 8px}'
    '.fl-card p{color:#3f4650;font-size:15px;line-height:23px;margin:0 0 10px}'
    '.fl-card p:last-child{margin-bottom:0}'
    '.fl-card ul{margin:0;padding:0 0 0 18px;color:#3f4650;font-size:15px;line-height:23px}'
    '.fl-card li{margin:0 0 6px}'
    '.fl-card li strong,.fl-list li strong{color:#1a1816}'
    '.fl-pill{display:inline-block;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;border-radius:9999px;padding:4px 10px;margin:0 6px 8px 0}'
    '.fl-pill--live{background:#e8f5ec;color:#0a801f}'
    '.fl-pill--soon{background:#f2f0ef;color:#3f4650}'
    '.fl-pill--get{background:#e8f5ec;color:#0a801f}'
    '.fl-pill--post{background:#fbe9ea;color:#d92228}'
    '.fl-pill--patch,.fl-pill--put{background:#fff3e0;color:#8a5a00}'
    '.fl-pill--del{background:#1a1816;color:#fff}'
    '.fl-table-wrap{border:1px solid #e5e5e5;border-radius:16px;background:#fff;overflow:hidden}'
    '.fl-table{width:100%;border-collapse:collapse;font-size:14px;line-height:21px}'
    '.fl-table thead{display:none}'
    '.fl-table,.fl-table tbody,.fl-table tr,.fl-table td{display:block}'
    '.fl-table tr{padding:16px;border-bottom:1px solid #e5e5e5}'
    '.fl-table tr:last-child{border-bottom:0}'
    '.fl-table td{padding:0 0 8px;color:#3f4650}'
    '.fl-table td:last-child{padding-bottom:0}'
    '.fl-table td:empty{display:none}'
    '.fl-table td[data-l]::before{content:attr(data-l);display:block;color:#1a1816;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 2px}'
    '.fl-table td.fl-td-m{padding-bottom:10px}'
    '.fl-table code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;color:#1a1816;word-break:break-all}'
    '@media(min-width:768px){.fl-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}'
    '.fl-table{display:table;min-width:720px}.fl-table tbody{display:table-row-group}.fl-table tr{display:table-row;padding:0}.fl-table td{display:table-cell;padding:12px 16px;border-bottom:1px solid #e5e5e5;vertical-align:top}'
    '.fl-table td:empty{display:table-cell}.fl-table td[data-l]::before{display:none}.fl-table td.fl-td-m{padding-bottom:12px}'
    '.fl-table thead{display:table-header-group}.fl-table th{background:#f2f0ef;color:#1a1816;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;text-align:left;padding:12px 16px;border-bottom:1px solid #e5e5e5}'
    '.fl-table tr:last-child td{border-bottom:0}.fl-table td:first-child{white-space:nowrap}.fl-table code{white-space:nowrap;word-break:normal}}'
    '.fl-list{max-width:820px;margin:0 auto;padding:0;list-style:none;counter-reset:fl}'
    '.fl-list li{position:relative;background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:20px 20px 20px 68px;margin:0 0 12px;color:#3f4650;font-size:15px;line-height:23px;counter-increment:fl}'
    '.fl-list li::before{content:counter(fl,decimal-leading-zero);position:absolute;left:20px;top:18px;width:32px;height:32px;border-radius:9999px;background:#fbe9ea;color:#d92228;font-weight:700;font-size:13px;display:inline-flex;align-items:center;justify-content:center}'
    '.fl-dark{background:#1a1816;color:#fff}'
    '.fl-dark .fl-head h2{color:#fff;opacity:1}.fl-dark .fl-head p{color:#beb8b0}'
    '.fl-code{background:#2b2b2b;border:1px solid #3f4650;border-radius:16px;padding:20px;overflow-x:auto;max-width:820px;margin:0 auto;box-sizing:border-box}'
    '.fl-code pre{margin:0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;line-height:21px;color:#f2f0ef;white-space:pre}'
    '.fl-code .c{color:#beb8b0}'
    '.fl-kv{display:grid;grid-template-columns:1fr;gap:6px 16px;margin:0;font-size:14px;line-height:22px}'
    '@media(min-width:768px){.fl-kv{grid-template-columns:auto 1fr}}'
    '.fl-kv dt{color:#1a1816;font-weight:700;margin:0}'
    '.fl-kv dd{color:#3f4650;margin:0 0 6px}'
    '@media(min-width:768px){.fl-kv dd{margin-bottom:0}}'
    '</style>'
)

HERO = f"""
<div class="pos_relative ov_hidden">
  <section aria-labelledby="fello-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="fello-hero-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px mb_16px">Fello, wired to drozq.</h1>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px max-w_640px m_0_auto">Every record the Fello API can read or write, every event it pushes, and the limits that decide what gets built.</p>
    </div>
  </section>
</div>
"""

STATS = f"""
<section id="status" aria-label="Fello API at a glance" class="bg_#fff py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-stats">
      <div class="fl-stat"><b>12</b><span>Endpoints, total</span></div>
      <div class="fl-stat"><b>10</b><span>Webhook events, live</span></div>
      <div class="fl-stat"><b>350,000</b><span>Requests a day</span></div>
      <div class="fl-stat"><b>100</b><span>Reads per 10 seconds</span></div>
    </div>
    <p class="fl-note">Key verified live on {PROBE_DATE}: <code>GET /webhooks</code> answered 200 with zero subscriptions registered, and the same call with no key answered 401. Base URL <code>https://api.fello.ai/public/v1</code>, one header, <code>x-api-key</code>. The client secret never touches an API call; it is the HMAC key that proves an inbound webhook came from Fello.</p>
  </div>
</section>
"""

THREE = """
<section id="directions" aria-labelledby="fello-dir-title" class="bg-c_#f2f0ef py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-head"><h2 id="fello-dir-title">Three directions. That is the whole API.</h2><p>Fello's API is a contact-sync API, not a data API. Feed it, read one record at a time, and listen.</p></div>
    <div class="fl-grid fl-grid--3">
      <div class="fl-card">
        <p class="fl-eyebrow">Push in</p>
        <h3>What I can write</h3>
        <ul>
          <li><strong>A contact:</strong> email (required), full name, phone, tags, one property address, an assigned user.</li>
          <li><strong>CRM link fields:</strong> name, url, source, stage, created date. Five fields, meant to point back at the Follow Up Boss record.</li>
          <li><strong>Tags:</strong> append, replace the whole set, or remove. Tags are the only lever into Fello's segments and workflows.</li>
          <li><strong>Properties:</strong> attach by free-text address (Fello parses and enriches it in the background), archive to pull it out of workflows.</li>
          <li><strong>Record status:</strong> Active or Monitored. Permanent delete.</li>
        </ul>
      </div>
      <div class="fl-card">
        <p class="fl-eyebrow">Pull out</p>
        <h3>What I can read</h3>
        <ul>
          <li><strong>One contact at a time</strong>, by email or by Fello id. There is no list, search, filter, or export.</li>
          <li><strong>Identity + hygiene:</strong> name, phone, email, email status (Valid, Invalid, Pending), record status, created date, proof-of-consent URL.</li>
          <li><strong>Engagement counters:</strong> form submissions, email sends, opens, clicks, dashboard views, dashboard clicks, each with its last date.</li>
          <li><strong>Lead score</strong> (0 to 100, read-only) and the tag set.</li>
          <li><strong>Properties:</strong> parsed address (unit, street, city, county, state, ZIP) and the property id. Address only, no value, no facts.</li>
        </ul>
      </div>
      <div class="fl-card">
        <p class="fl-eyebrow">Hear back</p>
        <h3>What Fello pushes to me</h3>
        <ul>
          <li><strong>Ten live events</strong> over HTTPS webhooks: a form submitted, a dashboard or email CTA clicked, a postcard scanned, an unsubscribe, an enrichment, a detail change, tags added or removed, a Felix AI handoff.</li>
          <li><strong>Three per event</strong>, HMAC-signed with the client secret, 2xx expected within 5 seconds, retried for hours, then dropped.</li>
          <li><strong>Announced, not live:</strong> dashboard viewed, assigned user changed, note added.</li>
        </ul>
      </div>
    </div>
  </div>
</section>
"""

ENDPOINTS = [
    ("post", "POST", "/contact", "Create a contact with basic details, tags, one address, CRM link fields, assigned user.", "Returns the full record plus warnings such as InvalidInputAddress. Duplicate email: 400 DuplicateContact."),
    ("get", "GET", "/contact?emailId= | ?contactId=", "Read one contact: identity, status, tags, engagement, properties, CRM fields, lead score.", "The only read. 404 ContactDoesNotExist."),
    ("patch", "PATCH", "/contact/{contactId}", "Update name, phone, email, CRM fields, assigned user, record status.", "Only the fields sent are touched."),
    ("del", "DELETE", "/contact/{contactId}", "Delete the contact and everything attached to it.", "Permanent. Does not propagate through the FUB sync."),
    ("post", "POST", "/contact/{contactId}/tags", "Append tags.", "Existing tags untouched."),
    ("put", "PUT", "/contact/{contactId}/tags", "Replace the whole tag set.", "Overwrites."),
    ("del", "DELETE", "/contact/{contactId}/tags", "Remove the listed tags.", "Others stay."),
    ("post", "POST", "/contact/{contactId}/property", "Attach a property by address (max 128 chars).", "Enrichment lands seconds later. 400 InvalidAddress / DuplicateProperty."),
    ("post", "POST", "/contact/property/{propertyId}/archive", "Archive a property so it leaves active workflows.", "404 PropertyDoesNotExist."),
    ("get", "GET", "/webhooks", "List subscriptions: id, url, event, status (Active, Removed, Failing).", ""),
    ("post", "POST", "/webhooks", "Subscribe a URL to one event type.", "HTTPS only. Max 3 per event."),
    ("del", "DELETE", "/webhooks/{subscriptionId}", "Unsubscribe.", ""),
]


def endpoint_rows() -> str:
    rows = []
    for cls, method, path, what, note in ENDPOINTS:
        rows.append(
            f'<tr><td class="fl-td-m"><span class="fl-pill fl-pill--{cls}">{method}</span></td>'
            f'<td data-l="Path"><code>{path}</code></td><td data-l="What it does">{what}</td>'
            + (f'<td data-l="Notes">{note}</td>' if note else '<td></td>') + '</tr>'
        )
    return "\n".join(rows)


TABLE = f"""
<section id="endpoints" aria-labelledby="fello-ep-title" class="bg_#fff py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-head"><h2 id="fello-ep-title">All twelve endpoints.</h2><p>Base <span class="fl-inline">https://api.fello.ai/public/v1</span>, JSON in and out, <span class="fl-inline">x-api-key</span> on every call.</p></div>
    <div class="fl-table-wrap">
      <table class="fl-table">
        <thead><tr><th>Method</th><th>Path</th><th>What it does</th><th>Notes</th></tr></thead>
        <tbody>
{endpoint_rows()}
        </tbody>
      </table>
    </div>
    <p class="fl-note">Errors come back as <code>{{code, message}}</code>: ContactDoesNotExist, PropertyDoesNotExist, InvalidAddress, DuplicateProperty, DuplicateContact, InvalidRequest (with a data object explaining the validation), 429 on a rate-limit breach, 5xx on Fello's side.</p>
  </div>
</section>
"""

RECORD = """
<section id="record" aria-labelledby="fello-rec-title" class="bg-c_#f2f0ef py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-head"><h2 id="fello-rec-title">The contact record, field by field.</h2><p>Everything a single read returns. This is the entire data surface.</p></div>
    <div class="fl-grid fl-grid--2">
      <div class="fl-card">
        <p class="fl-eyebrow">Identity</p>
        <dl class="fl-kv">
          <dt>contactId</dt><dd>Fello's id. Needed for every update, tag, and property call.</dd>
          <dt>name, phone, email</dt><dd>Phone must match a North American pattern; email is the duplicate key.</dd>
          <dt>emailStatus</dt><dd>Valid, Invalid, or Pending (validation runs after the write).</dd>
          <dt>recordStatus</dt><dd>Active or Monitored.</dd>
          <dt>createdAt</dt><dd>ISO timestamp.</dd>
          <dt>assignedUserEmailId</dt><dd>The Fello user who owns the contact.</dd>
          <dt>proofOfConsentUrl</dt><dd>Fello's consent record for the contact.</dd>
          <dt>tags</dt><dd>Free-text strings, e.g. HOT LEAD.</dd>
        </dl>
      </div>
      <div class="fl-card">
        <p class="fl-eyebrow">Engagement</p>
        <dl class="fl-kv">
          <dt>leadScore</dt><dd>0 to 100. Read-only.</dd>
          <dt>numOfFormSubmissions</dt><dd>+ lastFormSubmissionDate</dd>
          <dt>numOfEmailSends</dt><dd>+ lastEmailSentDate</dd>
          <dt>numOfEmailOpens</dt><dd>+ lastEmailOpenDate</dd>
          <dt>numOfEmailClicks</dt><dd>+ lastEmailClickDate</dd>
          <dt>numOfDashboardViews</dt><dd>+ lastDashboardViewedDate</dd>
          <dt>numOfDashboardClicks</dt><dd>+ lastDashboardClickedDate</dd>
        </dl>
      </div>
      <div class="fl-card">
        <p class="fl-eyebrow">Properties</p>
        <dl class="fl-kv">
          <dt>propertyId</dt><dd>Needed to archive.</dd>
          <dt>address</dt><dd>aptOrUnitNumber, streetAddress, city, county, state, zip. Parsed by Fello from the free-text address you sent.</dd>
        </dl>
        <p style="margin-top:12px">No value, no equity, no mortgage, no beds or baths. Fello's home intelligence stays inside Fello and the Follow Up Boss sync.</p>
      </div>
      <div class="fl-card">
        <p class="fl-eyebrow">CRM link</p>
        <dl class="fl-kv">
          <dt>crmFields.name</dt><dd>e.g. FollowUpBoss</dd>
          <dt>crmFields.url</dt><dd>Deep link to the CRM record.</dd>
          <dt>crmFields.source</dt><dd>e.g. drozq.com</dd>
          <dt>crmFields.stage</dt><dd>e.g. Lead</dd>
          <dt>crmFields.createdDate</dt><dd>ISO timestamp.</dd>
        </dl>
        <p style="margin-top:12px">Five fields, fixed. Not a custom-field store.</p>
      </div>
    </div>
  </div>
</section>
"""

EVENTS = [
    ("FormSubmission", "A contact submits any Fello form (landing page, widget, dashboard form).", "Run it through the drozq lead pipeline: alert, Follow Up Boss event, drip enrollment."),
    ("DashboardClick", "A contact clicks a call to action inside their home-value dashboard.", "Hot signal. Text Joshua, tag the FUB person."),
    ("EmailClick", "A contact clicks a call to action in a Fello email.", "Hot signal. Same handling as a dashboard click."),
    ("PostcardScan", "A contact scans or types a postcard URL.", "Hot signal from the mail campaign, if postcards ever run."),
    ("ContactUnsubscribed", "A contact opts out of Fello communications.", "Pause the drozq drip for the same email."),
    ("ContactEnriched", "Fello finishes enriching a contact with new data.", "Refresh the FUB record."),
    ("ContactDetailsUpdated", "Name, email, or phone changed in Fello.", "Mirror to FUB."),
    ("TagsAdded", "One or more tags added.", "Keep tag state in sync with the CRM."),
    ("TagsRemoved", "One or more tags removed.", "Same."),
    ("FelixAIHandoff", "Felix AI hands a conversation to a human.", "Highest-priority alert: a live conversation is waiting."),
]


def event_cards() -> str:
    cards = []
    for name, trigger, use in EVENTS:
        cards.append(
            f'<div class="fl-card"><span class="fl-pill fl-pill--live">Live</span>'
            f'<h3><code class="fl-inline">{name}</code></h3><p>{trigger}</p><p><strong>On drozq:</strong> {use}</p></div>'
        )
    for name in ("Dashboard Viewed", "Assigned User Changed", "Note Added"):
        cards.append(
            f'<div class="fl-card fl-card--warm"><span class="fl-pill fl-pill--soon">Announced</span>'
            f'<h3>{name}</h3><p>Listed by Fello as coming soon. Not subscribable yet.</p></div>'
        )
    return "\n".join(cards)


WEBHOOKS = f"""
<section id="webhooks" aria-labelledby="fello-wh-title" class="bg_#fff py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-head"><h2 id="fello-wh-title">Ten events Fello will push. Three more promised.</h2><p>Each arrives as a JSON POST with an events array; the body is signed with the client secret in the <span class="fl-inline">fello-webhook-signature</span> header.</p></div>
    <div class="fl-grid fl-grid--3">
{event_cards()}
    </div>
    <p class="fl-note">Delivery contract: answer 2xx within 5 seconds (the docs say 10 in one place and 5 in another, so build for 5) and do the real work afterwards. Anything else is retried at varying intervals for up to 8 hours, then the event is gone. A URL that keeps failing is unsubscribed automatically with an email notice. The docs publish only sample payload shapes, so capture real payloads on a catch-all URL before writing parsers.</p>
  </div>
</section>
"""

LIMITS = """
<section id="limits" aria-labelledby="fello-lim-title" class="bg-c_#f2f0ef py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-head"><h2 id="fello-lim-title">The limitations, stated flat.</h2><p>What these keys cannot do, so nothing gets designed around a door that is not there.</p></div>
    <ol class="fl-list">
      <li><strong>No list, search, filter, or export.</strong> Reads are one contact at a time by email or id. "Pull my whole Fello database" is not an API job; use the in-app export or the Follow Up Boss sync.</li>
      <li><strong>No home value, equity, mortgage, or property facts through the API.</strong> The AVM, the equity estimate, the likely-to-sell signal, and the enriched home facts never leave Fello through these twelve endpoints. Properties come back as a parsed address only. The way out is the native Follow Up Boss sync, mapped to custom fields, read back through FUB (see below).</li>
      <li><strong>No outbound actions.</strong> Nothing sends an email, a postcard, or a Felix call, and nothing starts a workflow directly. Tags are the only handle into Fello's automations.</li>
      <li><strong>No notes, no timeline writes, no lead-score writes.</strong> The lead score is read-only and the CRM fields are a fixed five-field link, not custom fields.</li>
      <li><strong>No sandbox.</strong> A dev host is listed in the docs but no test account exists, so every call hits the live account. Duplicate email returns 400 and creates nothing; a changed email creates a second person.</li>
      <li><strong>Webhooks are best-effort.</strong> Three subscriptions per event, HTTPS only, sample payloads only, a retry window measured in hours. A receiver that is down long enough loses events.</li>
      <li><strong>One key is the whole account.</strong> No scopes, no per-app permissions, no IP allow-list. The key lives in Cloudflare env vars and a gitignored file, nowhere else.</li>
      <li><strong>Enrichment is asynchronous.</strong> Read a contact right after creating it and the email status can be Pending with an empty enrichment; give it a few seconds.</li>
      <li><strong>Rate limits are generous but real.</strong> 100 reads and 50 writes per sliding 10 seconds per app, 350,000 calls a day per account, 429 with back-off on breach. Fello raises limits on request.</li>
      <li><strong>Deletes are permanent and never cross the Follow Up Boss sync.</strong> Fello's own guide says deletes do not propagate in either direction.</li>
    </ol>
  </div>
</section>
"""

BUILD = """
<section id="build" aria-labelledby="fello-build-title" class="bg_#fff py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-head"><h2 id="fello-build-title">Wired, as of September 2, 2026.</h2><p>All four steps are live on the site. The native Follow Up Boss sync carries the dollar figures; this is everything the API adds on top.</p></div>
    <div class="fl-grid fl-grid--2">
      <div class="fl-card fl-card--warm">
        <p class="fl-eyebrow">01 &middot; Live</p>
        <h3>Every drozq lead into Fello, the moment it lands</h3>
        <p>The lead handler pushes each real lead (funnel, valuation, net sheet, One Tap) as a Fello contact: name, E.164 phone, the confirmed street address, CRM link fields, and the tag vocabulary. A repeat email gets its tags appended and the address attached instead of a duplicate. Newsletter sign-ups never go.</p>
      </div>
      <div class="fl-card fl-card--warm">
        <p class="fl-eyebrow">02 &middot; Live</p>
        <h3>The webhook receiver at /api/fello/webhook</h3>
        <p>Signature-verified, 200 in milliseconds, work behind the response. Fello form submissions become drozq leads (alert, Follow Up Boss event, drip). Dashboard clicks, email clicks, postcard scans, and Felix handoffs send a hot alert with score, phone, and property, and tag the FUB person. Unsubscribes pause the drozq drip. Enrichment, detail changes, and tags refresh the FUB person quietly.</p>
      </div>
      <div class="fl-card fl-card--warm">
        <p class="fl-eyebrow">03 &middot; Live</p>
        <h3>One tag vocabulary</h3>
        <p>Drozq Website, then Seller or Buyer, then the mode (Sell, Buy, Sell + Buy, Valuation, Net Sheet, One Tap), the timeline bucket (Now, 1-3 mo, 4+ mo, Curious), the page of origin, and Paid: Google when a click id is present. Applied on every push, so Fello segments and workflows key off the same words.</p>
      </div>
      <div class="fl-card fl-card--warm">
        <p class="fl-eyebrow">04 &middot; Live</p>
        <h3>Engagement on the operating dashboard</h3>
        <p>The newest hundred leads are swept through Fello every ten minutes and ranked hot first: a dashboard or email click inside seven days, then views, then lead score. Three numbers on the dashboard, the named call list in the CLI, and the Fello home value and equity attached per lead the moment the Follow Up Boss field mapping is on.</p>
      </div>
    </div>
  </div>
</section>

<section id="values" aria-labelledby="fello-values-title" class="bg-c_#f2f0ef py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-head"><h2 id="fello-values-title">Where the home values actually come out.</h2><p>Fello holds the AVM, estimated equity, mortgage balance, rate, and refinance savings per property. They leave through these doors and no others.</p></div>
    <div class="fl-grid fl-grid--2">
      <div class="fl-card">
        <p class="fl-eyebrow">The sanctioned path</p>
        <h3>Fello to Follow Up Boss, then the FUB API</h3>
        <p>Connect Follow Up Boss inside Fello with the personal FUB owner key. In Field Mapping, map Home Value, Estimated Equity, Mortgage Balance, Lead Score, and Intent to new FUB custom fields. From that moment the engagement endpoint reads those fields per lead and the call list prints them. Enable the Fello embedded app in FUB and every contact record shows the AVM, price history, ownership, owner match, and equity on a card.</p>
      </div>
      <div class="fl-card">
        <p class="fl-eyebrow">What the events carry</p>
        <h3>The visitor's own answers, not the AVM</h3>
        <p>A form submission arrives with everything the homeowner typed: beds, baths, square feet, year built, conditions, remodels, HOA, pool, sale timeline, buying with selling, remarks, and what they think the home is worth. The receiver forwards all of it into the lead record.</p>
      </div>
      <div class="fl-card">
        <p class="fl-eyebrow">The signal leak</p>
        <h3>Fello's auto tags</h3>
        <p>Within a minute of creating a contact, Fello tagged the test record FELLO TARGET HOMEOWNER ORANGE and FELLO HIGH OWNER MATCH. High equity is in the same family. These ride the contact read and the tags webhook, and the call list shows them as signals.</p>
      </div>
      <div class="fl-card">
        <p class="fl-eyebrow">The counterweight</p>
        <h3>The site already values any address</h3>
        <p>The instant valuation and the net sheet compute their own numbers for every address a lead gives. Fello's job is the nurture behind the number: the living dashboard, the monthly email, the postcards, Felix.</p>
      </div>
    </div>
  </div>
</section>
"""

CLI = """
<section id="cli" aria-labelledby="fello-cli-title" class="fl-dark py_48px md:py_64px">
  <div class="fl-wrap">
    <div class="fl-head"><h2 id="fello-cli-title">The keys are already usable.</h2><p>scripts/fello.py reads the gitignored secret file and wraps all twelve endpoints, the webhook signature check, and the ranked call list.</p></div>
    <div class="fl-code"><pre><span class="c"># key check + live rate-limit budget</span>
python scripts/fello.py probe

<span class="c"># webhooks: list, subscribe every live event, unsubscribe</span>
python scripts/fello.py webhooks
python scripts/fello.py webhooks add-all https://drozq.com/api/fello/webhook
python scripts/fello.py webhooks rm &lt;subscriptionId&gt;

<span class="c"># contacts</span>
python scripts/fello.py contact get someone@example.com
python scripts/fello.py contact add someone@example.com --name "Full Name" \\
    --phone 9495551234 --address "1 Main St, Irvine, CA 92614" \\
    --tag "Drozq Website" --tag Seller --crm-source drozq.com
python scripts/fello.py tags add &lt;contactId&gt; "HOT LEAD"
python scripts/fello.py property add &lt;contactId&gt; "2 Main St, Irvine, CA 92614"

<span class="c"># verify a captured webhook (body on stdin)</span>
python scripts/fello.py verify "&lt;fello-webhook-signature&gt;" &lt; body.json

<span class="c"># the ranked engagement call list (hot first), values attached once FUB is mapped</span>
python scripts/fello.py calllist --csv</pre></div>
  </div>
</section>
"""

XREF_CSS = (
    '<style id="drozq-xref-css">.xr-band{padding:48px 0}.xr--warm{background:#f2f0ef}.xr--white{background:#fff}'
    '.xr-wrap{max-width:1035px;margin:0 auto;padding:0 32px;box-sizing:border-box}.xr-head{max-width:720px;margin:0 auto 28px;text-align:center}'
    '.xr-head h2{font-weight:800;opacity:.87;color:#2b2b2b;font-size:26px;line-height:34px;letter-spacing:.3px;margin:0 0 10px}'
    '.xr-head p{color:#3f4650;font-size:16px;line-height:26px;margin:0}.xr-grid{display:grid;grid-template-columns:1fr;gap:16px}'
    '.xr-card{display:block;background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:24px;text-decoration:none;color:inherit;'
    'transition:border-color .15s ease,transform .15s ease,box-shadow .15s ease;text-align:left;box-sizing:border-box}'
    '.xr--white .xr-card{background:#fbf8f4;border-color:#ece8e2}.xr-card:hover{border-color:#d92228;transform:translateY(-2px);box-shadow:0 8px 20px rgba(26,24,22,.08)}'
    '.xr-eyebrow{color:#d92228;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 8px}'
    '.xr-card h3{color:#1a1816;font-size:19px;line-height:26px;font-weight:700;margin:0 0 8px}.xr-card p{color:#3f4650;font-size:15px;line-height:23px;margin:0 0 10px}'
    '.xr-go{color:#d92228;font-weight:700;font-size:14px}.xr-a{color:#d92228;font-weight:700;text-decoration:underline;text-underline-offset:2px}'
    '@media (min-width:768px){.xr-band{padding:64px 0}.xr-head h2{font-size:32px;line-height:40px}.xr-grid--2{grid-template-columns:1fr 1fr;gap:20px}.xr-grid--3{grid-template-columns:1fr 1fr 1fr;gap:20px}}</style>'
)

XREF = """
<section class="xr-band xr--white"><div class="xr-wrap"><div class="xr-head"><h2>The rest of the plumbing.</h2><p>Where Fello plugs into what already runs.</p></div><div class="xr-grid xr-grid--3">
<a class="xr-card" href="/value/"><p class="xr-eyebrow">Instant</p><h3>The instant valuation</h3><p>The gated report every seller lead gets the moment they finish. Fello's dashboard picks up where it leaves off.</p><span class="xr-go">Open &rarr;</span></a>
<a class="xr-card" href="/net-sheet/"><p class="xr-eyebrow">Tool</p><h3>The seller net sheet</h3><p>County record, taxes, payoff, and the exact net. Another address-led lead surface to feed Fello.</p><span class="xr-go">Open &rarr;</span></a>
<a class="xr-card" href="/homes/"><p class="xr-eyebrow">Search</p><h3>Live MLS home search</h3><p>Buy-side leads from the IDX sign-up form, the same pipeline, the same tags.</p><span class="xr-go">Open &rarr;</span></a>
</div></div></section>
"""

CLOSING_HEAD = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Same door as every page</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Still guessing what it's worth?</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">Enter the address and the instant valuation lands the moment you finish.</p>

      <div id="fello-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">
"""

CLOSING_TAIL = """
        </div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px ta_center">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""

WEBPAGE_LD = (
    '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","name":"Fello API capabilities",'
    '"url":"https://drozq.com/fello/","description":"Internal reference for the Fello API on drozq.com.",'
    '"isPartOf":{"@type":"WebSite","@id":"https://drozq.com/#website"}}</script>'
)


def main() -> int:
    src = BASE.read_text(encoding="utf-8")

    def sub_once(pattern, repl, text, what):
        new, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"build_fello: expected exactly 1 {what}, got {n}")
        return new

    # --- the sell-mode closing pill, lifted verbatim from /short-sale/
    i = src.find('id="faq-closing-cta"')
    j = src.find("</form>", i)
    if i < 0 or j < 0:
        raise SystemExit("build_fello: could not find the /short-sale/ closing form to reuse")
    form = src[src.find("<form", i):j + len("</form>")]
    if form.count("Run my Valuation") != 1:
        raise SystemExit("build_fello: closing form label drifted; check /short-sale/")
    form = form.replace('placeholder="Enter your address" title="Enter your address"',
                        'placeholder="Enter the address you are selling" title="Enter the address you are selling"')

    # --- head ---------------------------------------------------------------
    src = sub_once(r"<title>[^<]*</title>", f"<title>{TITLE}</title>", src, "<title>")
    src = sub_once(r'<meta name="description" content="[^"]*">',
                   f'<meta name="description" content="{DESCRIPTION}">', src, "meta description")
    src = sub_once(r'<link rel="canonical" href="[^"]*">',
                   f'<link rel="canonical" href="{CANONICAL}"><meta name="robots" content="noindex,follow">',
                   src, "canonical")
    src = sub_once(r'<meta property="og:url" content="[^"]*">',
                   f'<meta property="og:url" content="{CANONICAL}">', src, "og:url")
    src = sub_once(r'<meta property="og:title" content="[^"]*">',
                   f'<meta property="og:title" content="{OG_TITLE}">', src, "og:title")
    src = sub_once(r'<meta property="og:description" content="[^"]*">',
                   f'<meta property="og:description" content="{OG_DESCRIPTION}">', src, "og:description")
    src = sub_once(r'<meta name="twitter:title" content="[^"]*">',
                   f'<meta name="twitter:title" content="{OG_TITLE}">', src, "twitter:title")
    src = sub_once(r'<meta name="twitter:description" content="[^"]*">',
                   f'<meta name="twitter:description" content="{OG_DESCRIPTION}">', src, "twitter:description")

    # --- page chrome + drop the short-sale-only styles ----------------------
    src = sub_once(r'<style id="drozq-page-chrome">.*?</style>', CHROME, src, "page chrome block")
    src = sub_once(r'<style id="shs-css">.*?</style>', "", src, "shs-css block")

    # --- main body ----------------------------------------------------------
    main_open = src.find("<main ")
    if main_open < 0:
        raise SystemExit("build_fello: could not find <main> in the base page")
    main_open_end = src.find(">", main_open) + 1
    main_close = src.find("</main>", main_open_end)
    if main_close < 0:
        raise SystemExit("build_fello: could not find </main> in the base page")

    body = (
        HERO + STATS + THREE + TABLE + RECORD + WEBHOOKS + LIMITS + BUILD + CLI
        + XREF_CSS + XREF + CLOSING_HEAD + form + CLOSING_TAIL + WEBPAGE_LD
    )
    out = src[:main_open_end] + "\n" + body + src[main_close:]

    # --- guardrails ---------------------------------------------------------
    if "—" in out:
        raise SystemExit("build_fello: em dash (U+2014) found. Banned.")
    for marker in ("DROZQ_FUNNEL_HTML_BEGIN", "DROZQ_FUNNEL_HTML_END",
                   "DROZQ_FUNNEL_JS_BEGIN", "DROZQ_FUNNEL_JS_END",
                   "DROZQ_HEADER_BEGIN", "DROZQ_HEADER_END",
                   "DROZQ_FOOTER_BEGIN", "DROZQ_FOOTER_END",
                   "DROZQ_NAV_JS_BEGIN", "DROZQ_NAV_JS_END",
                   "DROZQ_HEADER_JS_BEGIN", "DROZQ_HEADER_JS_END"):
        if out.count(marker) != 1:
            raise SystemExit(f"build_fello: marker {marker} count is {out.count(marker)}, expected 1")
    if out.count('name="robots"') != 1:
        raise SystemExit("build_fello: robots meta count is not 1")
    if "shs-" in out or "short sale" in out.lower():
        raise SystemExit("build_fello: short-sale residue found")
    if out.count("FAQPage") != 0:
        raise SystemExit("build_fello: FAQPage JSON-LD leaked from the base page")
    secret_file = ROOT / "scripts" / ".fello_secret"
    if secret_file.exists():
        import json
        sec = json.loads(secret_file.read_text(encoding="utf-8"))
        for v in (sec.get("api_key"), sec.get("client_secret")):
            if v and v in out:
                raise SystemExit("build_fello: a credential leaked into the page")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(out, encoding="utf-8")
    print(f"Built: fello/index.html ({len(out):,} chars, body {len(body):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
