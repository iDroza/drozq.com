"""Migrate /terms/ to the homepage template scaffold.

Content-first treatment, mirrors /privacy/: same legal-* scoped styles,
preserves the 17 sections of terms text, ends with an inline funnel-opening
form (no homepage redirect).
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page

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
  .legal-cta__pill button[type="submit"]:hover { background: #a92e2a; }
  .legal-cta__fineprint {
    font-size: 12px; color: #6b6864; margin: 12px 0 0;
  }
</style>

<section class="legal-hero">
  <h1>Terms of Service</h1>
  <p class="meta">Effective May 22, 2026 &middot; Last updated May 22, 2026 &middot; drozq.com</p>
</section>

<section class="legal-body">
  <div class="legal-inner">

    <section>
      <h2>Acceptance of Terms</h2>
      <p>By accessing or using <strong>drozq.com</strong> (the &ldquo;Site&rdquo;), you agree to these Terms of Service. If you do not agree, please do not use the Site. These terms apply to all visitors, including those who submit forms, request a home valuation, or otherwise contact us through the Site.</p>
      <p>We may update these terms from time to time. The &ldquo;Last updated&rdquo; date at the top reflects the most recent revision. Continued use of the Site after a change means you accept the updated terms.</p>
    </section>

    <section>
      <h2>About Us</h2>
      <p><strong>Joshua Guerrero</strong> is a licensed REALTOR&reg; in the State of California (DRE License #02267255), practicing under <strong>Real Brokerage</strong>. This Site is operated by Joshua Guerrero for the purpose of marketing real estate services and connecting with prospective clients.</p>
      <p><strong>Office:</strong> 17875 Von Karman Avenue, Suite 150, Irvine, CA 92614, USA<br>
      <strong>Contact:</strong> <a href="mailto:Josh@Drozq.com">Josh@Drozq.com</a> &middot; <a href="tel:9494385948">(949) 438-5948</a></p>
    </section>

    <section>
      <h2>Services</h2>
      <p>The Site provides marketing content, market data, educational material, and a way to request a no-obligation home valuation or consultation. Submitting a form is a request to be contacted; it is not a listing agreement, buyer-representation agreement, or any other binding contract for real estate services. Any agency relationship begins only when both parties sign a written representation agreement.</p>
      <p>No content on the Site constitutes legal, tax, financial, or investment advice. Consult a qualified attorney, CPA, or financial advisor for advice specific to your situation.</p>
    </section>

    <section>
      <h2>Real Estate Information Disclaimer</h2>
      <p><strong>Property information.</strong> Listing data, market statistics, comparable sales, neighborhood data, and similar information shown on the Site are drawn from sources we believe to be reliable, including the Multiple Listing Service (MLS), public records, and third-party data providers. We do not warrant the accuracy, completeness, or timeliness of any such information. Always verify property details independently before making any real estate decision.</p>
      <p><strong>Home valuations.</strong> Estimates produced through the Site, including comparative market analyses (&ldquo;CMAs&rdquo;) provided after a form submission, are opinions of value based on available data and an agent&rsquo;s judgment. They are not appraisals and should not be relied upon as such. An accurate determination of market value requires a licensed appraiser.</p>
      <p><strong>Past performance.</strong> Any results, statistics, case studies, or testimonials shown on the Site reflect past transactions and are not a guarantee of future results. Every real estate transaction is different.</p>
    </section>

    <section>
      <h2>Communications and Consent</h2>
      <p>When you submit a form on the Site, you agree that we may contact you by email, phone, and SMS about your inquiry and related real estate services, including by automated technology where permitted. Consent to receive marketing communications is not a condition of receiving real estate services.</p>
      <p><strong>Email:</strong> unsubscribe at any time using the link in any marketing email.<br>
      <strong>SMS:</strong> reply <strong>STOP</strong> to opt out. Standard message and data rates from your carrier may apply.</p>
      <p>Our handling of your contact information is described in our <a href="/privacy/">Privacy Policy</a>.</p>
    </section>

    <section>
      <h2>Fair Housing</h2>
      <p>Joshua Guerrero is committed to compliance with the federal <strong>Fair Housing Act</strong>, the California <strong>Fair Employment and Housing Act (FEHA)</strong>, and the California <strong>Unruh Civil Rights Act</strong>. Real estate services are provided without discrimination on the basis of race, color, religion, sex, disability, familial status, national origin, ancestry, sexual orientation, gender identity, gender expression, marital status, age, medical condition, genetic information, citizenship, primary language, immigration status, source of income, military or veteran status, or any other characteristic protected under federal or California law.</p>
    </section>

    <section>
      <h2>Permitted Use</h2>
      <p>You may view, print, and download Site content for personal, non-commercial use. You agree not to:</p>
      <p>&ndash; Scrape, harvest, or otherwise extract large portions of the Site by automated means.<br>
      &ndash; Reproduce, republish, or redistribute Site content for commercial purposes without prior written permission.<br>
      &ndash; Use the Site to transmit unlawful, harmful, harassing, or fraudulent material, or to interfere with the Site&rsquo;s operation or security.<br>
      &ndash; Submit a form using someone else&rsquo;s contact information without their authorization.</p>
    </section>

    <section>
      <h2>Intellectual Property</h2>
      <p>All Site content, including text, photographs, graphics, logos, design elements, and source code, is owned by Joshua Guerrero or licensed to us, and is protected by U.S. copyright and trademark law. The marks &ldquo;Drozq&rdquo; and the Drozq logo are used by Joshua Guerrero. Third-party trademarks shown on the Site (including REALTOR&reg;, MLS, and brokerage marks) remain the property of their respective owners.</p>
    </section>

    <section>
      <h2>Third-Party Links and Embeds</h2>
      <p>The Site may link to or embed content from third-party services, including Google Maps, Google Tag Manager, PostHog (analytics and session replay routed through <code>t.drozq.com</code>), and the MLS. We do not control these services and are not responsible for their content, accuracy, policies, or availability. Your use of a third-party service is subject to that service&rsquo;s own terms.</p>
    </section>

    <section>
      <h2>No Warranty</h2>
      <p>The Site is provided <strong>&ldquo;as is&rdquo;</strong> and <strong>&ldquo;as available,&rdquo;</strong> without warranties of any kind, whether express or implied, including warranties of merchantability, fitness for a particular purpose, title, and non-infringement. We do not warrant that the Site will be uninterrupted, error-free, secure, or free of viruses or harmful components, and we do not warrant the accuracy or reliability of any information shown.</p>
    </section>

    <section>
      <h2>Limitation of Liability</h2>
      <p>To the fullest extent permitted by law, Joshua Guerrero, Real Brokerage, and their respective affiliates, employees, and agents will not be liable for any indirect, incidental, special, consequential, exemplary, or punitive damages arising out of or related to your use of the Site, even if advised of the possibility of such damages. Our total liability arising out of or relating to the Site, regardless of the legal theory, will not exceed one hundred U.S. dollars (USD $100).</p>
      <p>Some jurisdictions do not allow the exclusion or limitation of certain damages, so the above limitations may not apply to you in full.</p>
    </section>

    <section>
      <h2>Indemnification</h2>
      <p>You agree to indemnify and hold harmless Joshua Guerrero and Real Brokerage from any claim, demand, loss, or expense (including reasonable attorneys&rsquo; fees) arising out of your misuse of the Site, your violation of these terms, or your violation of any law or the rights of a third party.</p>
    </section>

    <section>
      <h2>Governing Law and Venue</h2>
      <p>These terms are governed by the laws of the <strong>State of California</strong>, without regard to its conflict-of-laws principles. Any dispute arising out of or relating to the Site or these terms shall be brought exclusively in the state or federal courts located in <strong>Orange County, California</strong>, and you consent to the personal jurisdiction of those courts.</p>
    </section>

    <section>
      <h2>Severability</h2>
      <p>If any provision of these terms is held to be unenforceable, that provision will be enforced to the maximum extent permitted and the remaining provisions will remain in full force and effect.</p>
    </section>

    <section>
      <h2>Changes to These Terms</h2>
      <p>We may update these terms at any time by posting a revised version on this page. When we do, we will update the &ldquo;Effective&rdquo; and &ldquo;Last updated&rdquo; dates above. We encourage you to review these terms periodically.</p>
    </section>

    <section>
      <h2>Contact</h2>
      <p><strong>Joshua Guerrero</strong><br>
      Real Brokerage<br>
      CA DRE License #02267255<br>
      17875 Von Karman Avenue, Suite 150<br>
      Irvine, CA 92614, USA</p>
      <p><a href="mailto:Josh@Drozq.com">Josh@Drozq.com</a> &middot; <a href="tel:9494385948">(949) 438-5948</a></p>
    </section>

    <section>
      <h2>Legal Notice</h2>
      <p>These terms reflect our current site practices. They are not legal advice. For legal questions about your specific rights, consult an attorney.</p>
      <p><strong>Last updated:</strong> May 22, 2026</p>
    </section>

    <div class="legal-cta">
      <p class="legal-cta__lead">Thinking about selling?</p>
      <div id="tabpanel-sell" role="tabpanel" aria-labelledby="tab-sell">
        <form class="pos_relative">
          <div class="legal-cta__pill">
            <input type="text" name="location" placeholder="Enter your address"
                   autocomplete="off" aria-label="Enter your address">
            <button type="submit">Compare Agents</button>
          </div>
          <input type="hidden" name="gclid" value="">
        </form>
      </div>
      <p class="legal-cta__fineprint">Free CMA. No spam, no autodialer.</p>
    </div>

  </div>
</section>
"""

if __name__ == "__main__":
    scaffold_page(
        target="terms/index.html",
        title="Terms of Service | Joshua Guerrero, Real Brokerage",
        description="Terms of Service for drozq.com. Site usage, real estate disclaimers, lead-submission terms, and governing law for Joshua Guerrero, Real Brokerage.",
        canonical="/terms/",
        main_body_html=MAIN_BODY,
        og_title="Terms of Service | Joshua Guerrero",
        og_description="Terms of Service for drozq.com covering site usage, real estate disclaimers, and governing law.",
        noindex=True,
    )
