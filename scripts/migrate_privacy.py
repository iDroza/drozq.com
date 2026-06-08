"""Migrate /privacy/ to the homepage template scaffold.

Content-first treatment: header + policy body + footer + inline funnel sync
markers. No 3-tab funnel hero (legal page).
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page

# Policy body — preserves the legal text but corrects the stale PostHog claim.
# The page-specific styling lives in a <style> island injected at the top of
# main so the rest of the page stays on homepage Panda CSS classes.
MAIN_BODY = """
<style>
  /* Scoped styles for /privacy/ and /terms/ legal pages. Inline-only so we
     do not pollute the Panda CSS layers. */
  .legal-hero { background: #f2f0ef; padding: 64px 32px; text-align: center; }
  @media (min-width: 768px) { .legal-hero { padding: 96px 32px; } }
  .legal-hero h1 {
    font-size: clamp(2rem, 5vw, 3rem); font-weight: 800; color: #1a1816;
    margin: 0 0 14px; letter-spacing: -0.5px;
  }
  .legal-hero .meta { color: #3f4650; font-size: 15px; }
  .legal-body { padding: 64px 24px; background: #fff; }
  @media (min-width: 768px) { .legal-body { padding: 96px 32px; } }
  .legal-inner { max-width: 850px; margin: 0 auto; }
  .legal-inner section { margin-bottom: 40px; }
  .legal-inner section:last-child { margin-bottom: 0; }
  .legal-inner h2 {
    font-size: clamp(1.25rem, 2.5vw, 1.625rem); font-weight: 700;
    color: #1a1816; margin: 0 0 14px; line-height: 1.25;
  }
  .legal-inner p {
    font-size: 17px; color: #3f4650; line-height: 1.75; margin: 0 0 14px;
  }
  .legal-inner p:last-child { margin: 0; }
  .legal-inner p strong { color: #1a1816; }
  .legal-inner a {
    color: #d92228; text-decoration: underline; font-weight: 600;
  }
  .legal-inner a:hover { color: #a92e2a; }
  .legal-inner code {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.875em; background: #f2f0ef; padding: 1px 6px;
    border-radius: 4px;
  }
  .legal-cta {
    margin-top: 48px; padding: 32px; background: #fbf8f4;
    border: 1px solid #ece8e2; border-radius: 16px; text-align: center;
  }
  .legal-cta p.legal-cta__lead {
    font-size: 18px; font-weight: 700; color: #1a1816; margin: 0 0 16px;
  }
  .legal-cta form { max-width: 540px; margin: 0 auto; }
  .legal-cta__pill {
    position: relative; display: flex; flex-direction: column;
    align-items: stretch; background: #fff; border-radius: 30px;
    box-shadow: 0 1px 5px rgba(0,0,0,0.11); overflow: hidden;
  }
  @media (min-width: 560px) {
    .legal-cta__pill { flex-direction: row; align-items: center; }
  }
  .legal-cta__pill input[name="location"] {
    flex: 1; height: 56px; padding: 0 24px; border: none;
    background: transparent; font-size: 16px; color: #1a1816;
    outline: none; font-family: inherit;
  }
  .legal-cta__pill button[type="submit"] {
    height: 48px; margin: 4px; padding: 0 28px;
    background: #d92228; color: #fff; border: none; cursor: pointer;
    border-radius: 9999px; font-size: 16px; font-weight: 700;
    letter-spacing: 0.3px; font-family: inherit;
  }
  @media (min-width: 560px) {
    .legal-cta__pill button[type="submit"] { height: 48px; }
  }
  .legal-cta__pill button[type="submit"]:hover { background: #a92e2a; }
  .legal-cta__fineprint {
    font-size: 12px; color: #6b6864; margin: 12px 0 0;
  }
</style>

<section class="legal-hero">
  <h1>Privacy Policy</h1>
  <p class="meta">Effective May 22, 2026 &middot; Last updated May 22, 2026 &middot; drozq.com</p>
</section>

<section class="legal-body">
  <div class="legal-inner">

    <section>
      <h2>Who We Are</h2>
      <p><strong>Joshua Guerrero</strong> is a licensed REALTOR&reg; in the State of California (DRE License #02267255), practicing under <strong>Real Brokerage</strong>. This privacy policy applies to drozq.com.</p>
      <p><strong>Office:</strong> 17875 Von Karman Avenue, Suite 150, Irvine, CA 92614, USA<br>
      <strong>Privacy contact:</strong> <a href="mailto:legal@drozq.com">legal@drozq.com</a><br>
      <strong>General contact:</strong> <a href="mailto:Josh@Drozq.com">Josh@Drozq.com</a> &middot; <a href="tel:9494385948">(949) 438-5948</a></p>
    </section>

    <section>
      <h2>What Data We Collect</h2>
      <p><strong>Information you submit through forms.</strong> When you fill out a home valuation form, contact form, or lead modal on this site, we collect: your name, email address, phone number, the property address you enter (including street, city, state, ZIP, and geocoded latitude/longitude if you select an autocomplete suggestion), the page you submitted from, a submission timestamp, and any marketing source or campaign identifiers passed with your session.</p>
      <p><strong>Information collected automatically.</strong> When you load a page, our analytics tools record your IP address, browser and device type, operating system, referring URL, pages viewed, time on page, clicks, form interactions, and approximate geolocation derived from your IP. Through PostHog (see below), we also record a synthetic replay of your session showing page navigation, clicks, scroll position, and form interactions.</p>
      <p><strong>Cookies and similar identifiers.</strong> We use first-party cookies set by this site and third-party cookies set through our Google Tag Manager container. See &ldquo;Cookies and Tracking&rdquo; below for details.</p>
    </section>

    <section>
      <h2>How We Collect It</h2>
      <p><strong>Directly from you</strong> when you submit a form. Submissions are sent to a lead-processing endpoint on this domain (<code>/api/lead</code>).</p>
      <p><strong>Through Google Tag Manager</strong> (container <code>GTM-KVV3R96P</code>), loaded on every page. The tags currently loaded through our container are Google Analytics 4, Google Ads measurement, and PostHog. The set of tags it activates may change over time.</p>
      <p><strong>Through PostHog</strong> (product analytics, web analytics, and session replay), routed through our subdomain <code>t.drozq.com</code>. Session replay records a synthetic rendering of your visit (page navigation, clicks, scroll, form interactions) so we can diagnose usability issues and improve our funnel. Form field values you type are intended to be masked in the replay; however, you should not rely on this masking for sensitive information you would not type into any web form.</p>
      <p><strong>Through Google Maps Places Autocomplete.</strong> When you type a property address into one of our forms, the characters you type are sent to Google to return address suggestions.</p>
      <p>We do <strong>not</strong> currently operate a Meta/Facebook pixel, TikTok pixel, Microsoft Clarity, or a consent-management platform such as Cookiebot or OneTrust on this site.</p>
    </section>

    <section>
      <h2>Why We Collect It</h2>
      <p><strong>Respond to your inquiry.</strong> Return a home valuation, answer a question, or schedule a consultation.</p>
      <p><strong>Deliver real estate services.</strong> List, market, or negotiate on your behalf, and comply with brokerage record-keeping duties imposed on California real estate licensees.</p>
      <p><strong>Marketing follow-up.</strong> Contact you by email, phone, or SMS about your request or closely related services you initiated.</p>
      <p><strong>Analytics and ad measurement.</strong> Understand which pages and marketing channels work, and improve the site over time.</p>
      <p><strong>Legal compliance.</strong> Meet tax, regulatory, and recordkeeping obligations, and respond to lawful requests.</p>
    </section>

    <section>
      <h2>Who We Share It With</h2>
      <p><strong>Google</strong>, via Google Tag Manager (analytics and ad measurement) and Google Maps Places API (address autocomplete).</p>
      <p><strong>PostHog</strong>, for product analytics, web analytics, and session replay. Data is routed through our subdomain <code>t.drozq.com</code>.</p>
      <p><strong>MailChannels</strong>, the transactional email provider that delivers your form submission to our inbox.</p>
      <p><strong>Real Brokerage</strong>, our brokerage of record, when required for transaction processing or regulatory compliance.</p>
      <p><strong>Service providers</strong>, the hosting provider for this site and any email or SMS vendor used to operate it and respond to inquiries. These providers are limited to processing data on our behalf.</p>
      <p><strong>Legal and regulatory authorities</strong>, when required by law, subpoena, court order, or to comply with a government investigation.</p>
      <p><strong>We do not sell your personal information</strong> for money, and we do not share your personal information with third parties for their own independent marketing purposes.</p>
    </section>

    <section>
      <h2>Your California Privacy Rights (CCPA / CPRA)</h2>
      <p>If you are a California resident, you have the following rights under the California Consumer Privacy Act (CCPA), as amended by the California Privacy Rights Act (CPRA):</p>
      <p><strong>Right to know.</strong> Request what personal information we have collected about you, where we got it, why we collected it, and the categories of recipients with whom we have shared it.</p>
      <p><strong>Right to delete.</strong> Request deletion of your personal information. Some categories may be exempt (for example, transaction records that California real estate licensees are required by law to retain).</p>
      <p><strong>Right to correct.</strong> Request correction of inaccurate personal information we hold about you.</p>
      <p><strong>Right to opt out of sale or sharing.</strong> Ask us not to &ldquo;sell&rdquo; or &ldquo;share&rdquo; your personal information for cross-context behavioral advertising, as those terms are defined under CCPA/CPRA. To exercise this right, email <a href="mailto:legal@drozq.com">legal@drozq.com</a> with the subject line <strong>&ldquo;Do Not Sell or Share My Personal Information.&rdquo;</strong></p>
      <p><strong>Right to non-discrimination.</strong> We will not deny you service, charge you a different price, or provide a lower quality of service because you exercised your privacy rights.</p>
    </section>

    <section>
      <h2>How to Exercise Your Rights</h2>
      <p>Email <a href="mailto:legal@drozq.com">legal@drozq.com</a> with the subject line &ldquo;Privacy Request&rdquo; and describe the right you want to exercise. To protect you, we may need to verify your identity before acting on the request; we will ask for information that reasonably matches what we already have on file.</p>
      <p>We will respond to a verifiable request within <strong>45 days</strong>, as required by California law. If we need more time, we will notify you and may take up to an additional 45 days.</p>
      <p>You may also authorize an agent to make a request on your behalf; the agent will need to provide written permission signed by you.</p>
    </section>

    <section>
      <h2>Cookies and Tracking</h2>
      <p>Our site uses cookies and similar technologies set by our Google Tag Manager container (<code>GTM-KVV3R96P</code>) and by PostHog (routed through <code>t.drozq.com</code>). These support site analytics, ad attribution, advertising measurement, and session replay. The specific cookies set and their expiration periods are controlled by Google and PostHog and may change; typical lifetimes range from the end of your session to approximately two years.</p>
      <p><strong>How to opt out or manage tracking:</strong></p>
      <p>&ndash; Use your browser&rsquo;s privacy settings to block or clear cookies, or enable Global Privacy Control / &ldquo;Do Not Track.&rdquo;</p>
      <p>&ndash; Opt out of Google advertising personalization at <a href="https://adssettings.google.com" target="_blank" rel="noopener">adssettings.google.com</a>.</p>
      <p>&ndash; Email <a href="mailto:legal@drozq.com">legal@drozq.com</a> to request exclusion from tracking, including session replay.</p>
      <p>We do not currently display a cookie-consent banner on this site.</p>
    </section>

    <section>
      <h2>Data Retention</h2>
      <p><strong>Active leads.</strong> We retain your contact and property information while you are actively engaged with us.</p>
      <p><strong>Closed transactions.</strong> California real estate licensees are required to maintain transaction records for a minimum of three years after closing. We retain complete transaction files for <strong>seven years</strong> in line with brokerage practice and tax recordkeeping.</p>
      <p><strong>Unconverted inquiries.</strong> If you submit a form and we do not proceed to a transaction, we retain your contact record for up to three years, after which it is deleted or anonymized.</p>
      <p><strong>Analytics data.</strong> Google Analytics retention follows the retention setting configured in the Google Analytics property, which by default ranges from two to fourteen months. PostHog session replays are retained for up to 90 days unless otherwise needed for debugging.</p>
    </section>

    <section>
      <h2>Data Security</h2>
      <p>We use reasonable administrative, technical, and physical safeguards to protect personal information against unauthorized access, disclosure, alteration, and destruction. This site is served over HTTPS, and access to lead data is limited to personnel who need it.</p>
      <p>No method of transmission over the internet is 100 percent secure, and we cannot guarantee absolute security. If we become aware of a security incident affecting your personal information, we will notify you as required by California&rsquo;s data-breach notification law.</p>
    </section>

    <section>
      <h2>Children&rsquo;s Privacy</h2>
      <p>This site is intended for adults interested in buying, selling, or learning about real estate. We do not knowingly collect personal information from children under the age of 16, and the site is not directed to children. If you believe we have inadvertently collected information from a child, please email <a href="mailto:legal@drozq.com">legal@drozq.com</a> and we will delete it promptly.</p>
    </section>

    <section>
      <h2>Fair Housing</h2>
      <p>Joshua Guerrero is committed to compliance with the federal <strong>Fair Housing Act</strong>, the California <strong>Fair Employment and Housing Act (FEHA)</strong>, and the California <strong>Unruh Civil Rights Act</strong>. Real estate services are provided without discrimination on the basis of race, color, religion, sex, disability, familial status, national origin, ancestry, sexual orientation, gender identity, gender expression, marital status, age, medical condition, genetic information, citizenship, primary language, immigration status, source of income, military or veteran status, or any other characteristic protected under federal or California law.</p>
    </section>

    <section>
      <h2>Email and SMS Communications</h2>
      <p>If you share your email address or phone number, you agree that we may contact you about your inquiry and related services. Unsubscribe from marketing email at any time using the link in the message. For SMS, reply <strong>STOP</strong> to opt out; standard message and data rates from your carrier may apply.</p>
    </section>

    <section>
      <h2>Changes to This Policy</h2>
      <p>We may update this policy from time to time. When we do, we will update the &ldquo;Effective&rdquo; and &ldquo;Last updated&rdquo; dates at the top of the page. Please review this policy periodically. Continued use of the site after a change means you accept the updated policy.</p>
    </section>

    <section>
      <h2>Contact Information</h2>
      <p><strong>Joshua Guerrero</strong><br>
      Real Brokerage<br>
      CA DRE License #02267255<br>
      17875 Von Karman Avenue, Suite 150<br>
      Irvine, CA 92614, USA</p>
      <p><strong>Privacy requests:</strong> <a href="mailto:legal@drozq.com">legal@drozq.com</a><br>
      <strong>General inquiries:</strong> <a href="mailto:Josh@Drozq.com">Josh@Drozq.com</a> &middot; <a href="tel:9494385948">(949) 438-5948</a></p>
    </section>

    <section>
      <h2>Legal Notice</h2>
      <p>This privacy policy reflects our current practices. It is not legal advice. For legal questions about your specific rights, consult an attorney.</p>
      <p><strong>Last updated:</strong> May 22, 2026</p>
    </section>

    <div class="legal-cta">
      <p class="legal-cta__lead">Thinking about selling?</p>
      <div id="tabpanel-sell" role="tabpanel" aria-labelledby="tab-sell">
        <form class="pos_relative">
          <div class="legal-cta__pill">
            <input type="text" name="location" placeholder="Enter your address"
                   autocomplete="off" aria-label="Enter your address">
            <button type="submit">See Plan</button>
          </div>
          <input type="hidden" name="gclid" value="">
        </form>
      </div>
      <p class="legal-cta__fineprint">Or call direct: <a href="tel:9494385948" style="color:#d92228;font-weight:700;text-decoration:none"><strong>(949) 438-5948</strong></a></p>
    </div>

  </div>
</section>
"""

if __name__ == "__main__":
    scaffold_page(
        target="privacy/index.html",
        title="Privacy Policy | Joshua Guerrero, Real Brokerage",
        description="Privacy Policy for drozq.com. How Joshua Guerrero collects, uses, and protects lead data, cookies, session replay, and California privacy rights.",
        canonical="/privacy/",
        main_body_html=MAIN_BODY,
        og_title="Privacy Policy | Joshua Guerrero",
        og_description="Privacy Policy for drozq.com covering data collection, cookies, session replay, and California privacy rights.",
        noindex=True,
    )
