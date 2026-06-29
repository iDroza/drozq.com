"""Migrate /field-notes/ to the homepage template scaffold.

Field Notes is the "blog" surface of the site, except not actually a blog
in the usual sense: posts go up when there's something worth saying, not
on a schedule. As of 2026-05-26 the page is a placeholder with three
upcoming notes in the queue plus an email subscribe form for ping-when-
new-posts-drop.

KILLED from the legacy page:
- Brand-mode (mint/navy/green/red) palette + custom CSS reset.
- "Top-Rated Listing Agent" topbar + brand-mode sticky header + the
  510-935-5701 phone + dropdown nav grid.
- Brand-mode hero (.fn-hero with gradient overlay) + .fn-queue +
  .fn-subscribe + .fn-crosslink + .cf-cta-strip styles, all replaced
  with homepage tokens / scoped style blocks.
- Brand-mode navy footer with 4-column grid + brokerage badge.
- "Book a 15-minute call -> /contact/" final CTA (replaced with the
  inline address-form pill so the page captures leads directly, matching
  every other migrated page).

PRESERVED + reframed:
- "What I'm seeing in the market this week." h1.
- "A field log." narrow centered copy with all 3 paragraphs verbatim.
- All 3 upcoming notes in the queue, verbatim (Note 001 Market Intel,
  Note 002 Operator Log, Note 003 Opinion).
- The email subscribe form, restyled to homepage tokens, still POSTs to
  /api/lead with the same hidden-field contract so subscribers continue
  to flow through MailChannels.
- Cross-link to /testimonials/ ("the long-form version").
- Blog + BreadcrumbList JSON-LD.

The subscribe form is a documented exception to the "inline 3-funnel is
the only lead-capture form on the site" rule in TEMPLATE.md section 12.
The intent here is "notify me when a note drops," not "compare agents."
Keeping the form preserves a real conversion path for a real audience.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page


# (number, category, title, teaser)
QUEUE_NOTES = [
    (
        "Note 001", "Market Intel",
        "What 14 days on market actually means in Irvine right now.",
        "A look at the real time-to-sell data for Irvine homes in the past 90 days, broken down by price band. The headline numbers everyone quotes are misleading.",
    ),
    (
        "Note 002", "Operator Log",
        "The inspection report that saved my client $11,000.",
        "A breakdown of how I read inspection reports differently than most agents, with an example from a recent transaction. The line item that everyone misses.",
    ),
    (
        "Note 003", "Opinion",
        "The Zestimate is the worst thing that ever happened to home valuation.",
        "An honest argument about why algorithmic home valuation tools have made sellers worse at pricing their homes, not better. And what to use instead.",
    ),
]


def landing_form_pill(placeholder: str, value: str = "") -> str:
    return f"""
    <form class="pos_relative">
      <div class="pos_relative d_flex flex-d_column xs:flex-d_row ai_center bg-c_#fff mb_16px xs:mb_0 h_48px sm:h_auto bdr_30px bx-sh_0_1px_5px_rgba(0,_0,_0,_.11)">
        <input name="location" placeholder="{placeholder}" title="{placeholder}" autocomplete="off"
               class="w_100% bd_none bg-c_transparent -webkit-appearance_none flex_1 focus:ring_none h_48px md:h_60px lh_48px md:lh_60px pt_16px md:pt_0 pb_16px md:pb_0 pl_16px md:pl_32px pr_32px xs:pr_8px mb_16px xs:mb_0 bdr-tl_30px bdr-bl_30px fs_14px md:fs_18px"
               value="{value}" aria-label="{placeholder}">
        <div class="w_100% xs:w_auto mr_0 md:mr_3px h_48px md:h_60px lh_48px md:lh_60px pos_absolute xs:pos_static top_60px xs:top_0">
          <button type="submit"
                  class="bg_primary c_white cursor_pointer w_100% xs:w_145px md:w_auto h_48px md:h_54px fs_13px md:fs_18px fw_bold bdr_full px_0px md:px_28px ls_0.5px d_block md:d_inline-flex ai_center gap_0px md:gap_10px hover:bg_primaryHover">
            See Plan
          </button>
        </div>
      </div>
      <input type="hidden" name="gclid" value="">
    </form>"""


HERO = f"""
<div class="pos_relative ov_hidden">
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_50%_55% [&_img]:[@media_(max-width:_480px)]:obj-p_center">
    <img src="/media/images/coastal-modern-home.webp" alt="Modern hillside home overlooking the Southern California coast at sunset" width="1672" height="941" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.4)"></div>
  </div>

  <section aria-labelledby="fn-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="fn-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">What I'm seeing in the market this week.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">Real observations from real transactions in Irvine and the South Bay.</p>
    </div>
  </section>

  <section aria-label="Compare agents" class="pos_relative z_1 pb_48px xs:pb_64px md:pb_80px">
    <div class="d_flex jc_center pl_32px pr_32px bx-s_border-box mb_24px">
      <div class="pos_relative w_100% max-w_700px">
        <div class="pos_relative" role="button" tabindex="0" aria-label="Property transaction type selector">
          <div class="d_flex jc_center gap_6px mb_0px">
            <div role="tablist" class="d_flex jc_center bdr_8px_8px_0_0 ov_hidden">
              <button role="tab" aria-selected="true"  aria-controls="tabpanel-sell"     id="tab-sell"     tabindex="0"
                      class="bdr_8px_8px_0_0 p_12px_16px fw_700 fs_13px lh_16px ta_center bg_#fff   c_#d92228 bd_none cursor_pointer as_flex-end [&:not(:first-child)]:ml_6px">Sell</button>
              <button role="tab" aria-selected="false" aria-controls="tabpanel-buy"      id="tab-buy"      tabindex="-1"
                      class="bdr_8px_8px_0_0 p_8px_16px  fw_700 fs_13px lh_16px ta_center bg_#d92228 c_#fff    bd_none cursor_pointer as_flex-end [&:not(:first-child)]:ml_6px [&:hover]:bg_#a92e2a">Buy</button>
              <button role="tab" aria-selected="false" aria-controls="tabpanel-sell-buy" id="tab-sell-buy" tabindex="-1"
                      class="bdr_8px_8px_0_0 p_8px_16px  fw_700 fs_13px lh_16px ta_center bg_#d92228 c_#fff    bd_none cursor_pointer as_flex-end [&:not(:first-child)]:ml_6px [&:hover]:bg_#a92e2a">Sell &amp; Buy</button>
            </div>
          </div>

          <div class="w_100% bdr_30px pos_relative min-h_60px">
            <div id="tabpanel-sell"     role="tabpanel" aria-labelledby="tab-sell"     class="d_block">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter the address you are selling")}</div>
            </div>
            <div id="tabpanel-buy"      role="tabpanel" aria-labelledby="tab-buy"      hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("City, neighborhood, or ZIP")}</div>
            </div>
            <div id="tabpanel-sell-buy" role="tabpanel" aria-labelledby="tab-sell-buy" hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter the address you are selling")}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>
"""


WHAT_THIS_IS = """
<section aria-labelledby="fn-what-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">What This Is</p>
    <h2 id="fn-what-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">A field log.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Most real estate blogs exist to game search engines. They're written by agents who don't write, for readers who don't read. This isn't that.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Field Notes is where I share what I'm actually seeing on the ground. The deal that almost fell apart and why. The market shift nobody is talking about yet. The opinion I'd share at the bar but that most agents are too cautious to put in writing.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Posts go up when there's something worth saying. Not on a schedule. Not for SEO. If you want to think about real estate the way I think about it, this is where to read.</p>
  </div>
</section>
"""


# Note card style. Panda CSS doesn't ship the grid-tc_repeat(3,_1fr)
# arbitrary value reliably (same pitfall as drozq-portrait-split). Use a
# scoped class block so the queue grid behaves correctly at desktop.
QUEUE_STYLE = """
<style>
.drozq-fn-queue {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 768px) { .drozq-fn-queue { grid-template-columns: repeat(3, 1fr); gap: 20px; } }
.drozq-fn-note {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 28px 26px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}
.drozq-fn-note__tab {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #d92228;
}
.drozq-fn-note__category {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #3f4650;
  margin: 0;
}
.drozq-fn-note__title {
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1.35;
  color: #1a1816;
  letter-spacing: -0.005em;
  margin: 0;
}
.drozq-fn-note__teaser {
  font-size: 0.95rem;
  line-height: 1.55;
  color: #3f4650;
  margin: 0;
}
.drozq-fn-note__footer {
  margin-top: auto;
  padding-top: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #757575;
  border-top: 1px dashed #e5e5e5;
}
</style>
"""


def note_card(num: str, category: str, title: str, teaser: str) -> str:
    return f"""
      <article class="drozq-fn-note" aria-hidden="true">
        <span class="drozq-fn-note__tab">{num}</span>
        <p class="drozq-fn-note__category">{category}</p>
        <h3 class="drozq-fn-note__title">{title}</h3>
        <p class="drozq-fn-note__teaser">{teaser}</p>
        <div class="drozq-fn-note__footer">Coming soon</div>
      </article>"""


QUEUE_SECTION = """
<section aria-labelledby="fn-queue-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">In the Queue</p>
      <h2 id="fn-queue-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The first three notes are being written.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Each one drops when it's actually ready. Subscribe below and you'll get a single email the moment a post goes live.</p>
    </div>

    <div class="drozq-fn-queue">
""" + "\n".join(note_card(n, c, t, te) for (n, c, t, te) in QUEUE_NOTES) + """
    </div>
  </div>
</section>
"""


# Subscribe form. Documented exception to the "inline 3-funnel only" rule
# in TEMPLATE.md section 12. Intent is "ping me when a note drops," not
# "compare agents." Still POSTs to /api/lead with the same hidden-field
# contract so subscribers flow through MailChannels.
SUBSCRIBE_STYLE = """
<style>
.drozq-fn-subscribe {
  max-width: 560px;
  margin: 0 auto;
}
.drozq-fn-subscribe__form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 24px 0 8px;
}
@media (min-width: 480px) {
  .drozq-fn-subscribe__form { flex-direction: row; gap: 0; }
}
.drozq-fn-subscribe__form input[type="email"] {
  flex: 1;
  height: 54px;
  padding: 0 18px;
  font-size: 16px;
  font-family: inherit;
  border: 1px solid #d3cfca;
  border-radius: 30px;
  background: #fff;
  outline: none;
  transition: border-color .2s ease;
  -webkit-appearance: none;
  min-width: 0;
}
@media (min-width: 480px) {
  .drozq-fn-subscribe__form input[type="email"] {
    border-radius: 30px 0 0 30px;
    border-right: none;
  }
}
.drozq-fn-subscribe__form input[type="email"]:focus { border-color: #d92228; }
.drozq-fn-subscribe__form button {
  height: 54px;
  padding: 0 32px;
  font-size: 16px;
  font-family: inherit;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: #d92228;
  color: #ffffff;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  transition: background-color .2s ease;
  white-space: nowrap;
}
.drozq-fn-subscribe__form button:hover { background: #a92e2a; }
.drozq-fn-subscribe__form button:disabled { background: #a8a39c; cursor: wait; }
.drozq-fn-subscribe__note {
  font-size: 13px;
  color: #757575;
  margin: 8px 0 0;
}
.drozq-fn-subscribe__error,
.drozq-fn-subscribe__success {
  display: none;
  font-size: 14px;
  margin: 12px 0 0;
  padding: 12px 16px;
  border-radius: 8px;
  text-align: left;
}
.drozq-fn-subscribe__error { background: #fbe9ea; color: #b81d22; }
.drozq-fn-subscribe__success { background: #e7f5e9; color: #0a801f; }
.drozq-fn-subscribe__error.is-visible,
.drozq-fn-subscribe__success.is-visible { display: block; }
</style>
"""


SUBSCRIBE_SECTION = """
<section aria-labelledby="fn-subscribe-title" id="fnSubscribe" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="drozq-fn-subscribe ta_center pl_32px md:pl_24px pr_32px md:pr_24px">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Stay in the Loop</p>
    <h2 id="fn-subscribe-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Get notes when they drop.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">One email when a new note goes up. No newsletter, no marketing sequences, just the post the moment it's live.</p>

    <form class="drozq-fn-subscribe__form" id="fnSubscribeForm" novalidate>
      <div style="position:absolute; left:-9999px;" aria-hidden="true">
        <input type="text" name="company_website" autocomplete="off" tabindex="-1">
      </div>

      <input type="email" name="email" placeholder="your@email.com" autocomplete="email" required aria-label="Your email address">
      <button type="submit">Notify me</button>

      <input type="hidden" name="name" value="Field Notes Subscriber">
      <input type="hidden" name="phone" value="Not provided">
      <input type="hidden" name="intent" value="Field Notes Subscribe">
      <input type="hidden" name="consent" value="yes">
      <input type="hidden" name="source" value="field-notes-subscribe">
      <input type="hidden" name="source_page" value="field-notes-subscribe">
      <input type="hidden" name="page_url" id="fnPageUrl">
      <input type="hidden" name="submitted_at" id="fnTimestamp">
    </form>

    <p class="drozq-fn-subscribe__note">Unsubscribe anytime. I will never share your email.</p>

    <div class="drozq-fn-subscribe__error" id="fnSubscribeError" role="alert">Something went wrong. Please try again, or email Josh@Drozq.com directly.</div>
    <div class="drozq-fn-subscribe__success" id="fnSubscribeSuccess" role="status"><strong>Thanks, you're on the list.</strong> I'll email you the moment the first note goes live.</div>
  </div>
</section>

<script>
(function() {
  var form = document.getElementById('fnSubscribeForm');
  if (!form) return;
  var errBox = document.getElementById('fnSubscribeError');
  var okBox  = document.getElementById('fnSubscribeSuccess');
  var pageUrl = document.getElementById('fnPageUrl');
  var ts = document.getElementById('fnTimestamp');

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    errBox.classList.remove('is-visible');
    okBox.classList.remove('is-visible');

    var btn = form.querySelector('button[type=submit]');
    var orig = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Sending...';

    if (pageUrl) pageUrl.value = window.location.href;
    if (ts) ts.value = new Date().toISOString();

    var data = new FormData(form);
    fetch('/api/lead', { method: 'POST', body: data })
      .then(function(r) { return r.json().then(function(j) { return { ok: r.ok, data: j }; }); })
      .then(function(res) {
        if (res.ok && res.data && res.data.ok) {
          form.style.display = 'none';
          okBox.classList.add('is-visible');
        } else {
          errBox.classList.add('is-visible');
        }
      })
      .catch(function() { errBox.classList.add('is-visible'); })
      .finally(function() {
        btn.disabled = false;
        btn.textContent = orig;
      });
  });
})();
</script>
"""


CROSSLINK = """
<style>
.btn-secondary-outline {
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent; color: #d92228;
  border: 1px solid #d92228;
  font-weight: 700; font-size: 14px; letter-spacing: 0.3px;
  padding: 10px 22px; border-radius: 9999px;
  text-decoration: none;
  transition: background-color .2s ease, color .2s ease;
}
.btn-secondary-outline:hover { background: #d92228; color: #fff; }
@media (min-width: 768px) { .btn-secondary-outline { font-size: 15px; } }
</style>
<section aria-labelledby="fn-crosslink-title" class="bg-c_#f2f0ef py_48px md:py_64px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Want the long-form version?</p>
    <h2 id="fn-crosslink-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_24px md:fs_30px ls_0.3px mb_16px">The case files.</h2>
    <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px mb_24px m_0_auto" style="max-width:560px;">Field Notes are the short, frequent version. The case files are the in-depth version, every transaction documented with the real numbers and the real outcome. If you want to see how the work actually gets done, start there.</p>
    <a href="/testimonials/" class="btn-secondary-outline">See the case files &rarr;</a>
  </div>
</section>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Closer than you think to selling?</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">If reading this far means you're starting to think about your own move, the next step is a five-minute address check. I'll send a real comp study within 24 hours.</p>
    </div>

    <div role="tablist" keyboard-select-mode="focus"
         class="d_flex jc_center pos_relative bg_#fff max-w_251px w_100% h_48px m_0_auto bdr_24px bx-sh_0_1px_5px_rgba(0,0,0,.11) mt_14px bd_1px_solid_#e5e5e5">
      <button id="sellTabBtn" role="tab" aria-controls="sellTab" aria-selected="true"  data-selected="true"  type="button"
              class="ap_none bd_none bg_transparent cursor_pointer max-w_125px max-h_42px w_100% p_10px_16px bdr_999px fs_14px md:fs_16px fw_700 lh_20px ta_center m_3px_3px_0 c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:bg-c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:c_#fff">I'm selling</button>
      <button id="buyTabBtn"  role="tab" aria-controls="buyTab"  aria-selected="false" data-selected="false" type="button"
              class="ap_none bd_none bg_transparent cursor_pointer max-w_125px max-h_42px w_100% p_10px_16px bdr_999px fs_14px md:fs_16px fw_700 lh_20px ta_center m_3px_3px_0 c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:bg-c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:c_#fff">I'm buying</button>
    </div>

    <div id="sellTab" role="tabpanel" aria-labelledby="sellTabBtn" class="d_block mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <ul class="d_flex flex-d_column gap_24px lg:gap_44px m_0 li-s_none p_0 mb_32px">
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">1</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A real comp study, not an algorithm.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">The 8-12 homes most like yours, adjusted line by line. The same read I'd send a paying client on day one.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A defensible list price, in plain English.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">What it's worth, what to fix, what to skip, and what to walk past on the listing photos.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">The decision stays yours.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">You read the study, you decide whether to list. I follow up only if you ask me to.</p>
          </div>
        </li>
      </ul>

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Enter your address to start the home value report.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("Your address")}</div>
    </div>

    <div id="buyTab" role="tabpanel" aria-labelledby="buyTabBtn" hidden class="d_none mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <ul class="d_flex flex-d_column gap_24px lg:gap_44px m_0 li-s_none p_0 mb_32px">
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">1</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A buying strategy, not a property list.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">I help you decide what you are actually buying for, then narrow the field with a written framework.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Offers structured to actually win.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Tight contingencies, clean appraisal language, and seller credits used where they move price.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Lender, inspector, and escrow already in place.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">A vetted bench of local partners means escrow runs on schedule and inspection reports come back in plain English.</p>
          </div>
        </li>
      </ul>

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Tell me where you want to buy.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("City, neighborhood, or ZIP", value="Irvine, CA")}</div>
    </div>

  </div>
</section>
"""


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Why read any of this?</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Because eventually you'll sell a home.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">And when that day comes, you'll want someone in your corner who reads the market this carefully every week. That's the whole point. If you're closer than you thought, let's talk.</p>

      <div id="fn-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


JSON_LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": "Field Notes",
  "description": "Short, observational notes from a working real estate agent. Market intelligence, operator logs, and unfiltered opinions on the Southern California real estate market.",
  "url": "https://drozq.com/field-notes/",
  "author": {
    "@type": "Person",
    "name": "Joshua Guerrero",
    "url": "https://drozq.com/about/"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Drozq",
    "url": "https://drozq.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://drozq.com/media/images/Waist.png"
    }
  },
  "inLanguage": "en-US"
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
    {"@type": "ListItem", "position": 2, "name": "Field Notes", "item": "https://drozq.com/field-notes/"}
  ]
}
</script>
"""


MAIN_BODY = (
    HERO
    + WHAT_THIS_IS
    + QUEUE_STYLE
    + QUEUE_SECTION
    + SUBSCRIBE_STYLE
    + SUBSCRIBE_SECTION
    + CROSSLINK
    + MID_TABS
    + CLOSING_CTA
    + JSON_LD
)


if __name__ == "__main__":
    scaffold_page(
        target="field-notes/index.html",
        title="Field Notes | Joshua Guerrero, Real Brokerage",
        description="Short, observational notes from a working real estate agent. Market intelligence, operator logs, and unfiltered opinions on the Southern California real estate market.",
        canonical="/field-notes/",
        main_body_html=MAIN_BODY,
        og_title="Field Notes | Joshua Guerrero",
        og_description="Short, observational notes from a working real estate agent. Market intel, operator logs, and unfiltered opinions.",
    )
