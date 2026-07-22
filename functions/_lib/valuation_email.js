// The instant valuation report email: what a funnel or /value/ lead receives
// the moment they submit, an automated mini-CMA rendered in the branded email
// template. The hand-built CMA from Joshua follows behind it (stated in the
// copy), so this email is the first half of the "both land in your inbox"
// promise. Transactional: no unsubscribe link, no tracking pixel.
//
// One canonical input shape (every field optional; the renderer degrades):
//   { street, formatted, trueValue, avmValue, avmLow, avmHigh,
//     assessorValue, assessorYear, rebuildValue, arvValue,
//     beds, baths, sqft, yearBuilt,
//     comps: [{ address, sqft, price, daysOld }],
//     soldCount, soldMedian, soldWindowMonths, moi, lean,
//     rentMonthly, capRate }

import { renderEmail, escapeHtml } from "./email.js";

const FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";

function money(n) {
  return (n == null || !isFinite(n)) ? null : "$" + Math.round(n).toLocaleString("en-US");
}

function ago(daysOld) {
  if (daysOld == null || !isFinite(daysOld)) return "";
  if (daysOld < 45) return Math.max(1, Math.round(daysOld)) + " days ago";
  return Math.round(daysOld / 30) + " mo ago";
}

// Normalize the /api/valuation JSON response into the renderer's input.
export function reportInputFromApiResponse(r) {
  const sys = (r && r.systems) || {};
  const prop = (r && r.property) || {};
  const stats = (r && r.cma && r.cma.stats) || {};
  const inv = (r && r.investor) || {};
  return {
    street: (r && r.address && r.address.street) || null,
    formatted: (r && r.address && r.address.formatted) || null,
    trueValue: sys.triangulated && sys.triangulated.value,
    avmValue: sys.marketAVM && sys.marketAVM.value,
    avmLow: sys.marketAVM && sys.marketAVM.rangeLow,
    avmHigh: sys.marketAVM && sys.marketAVM.rangeHigh,
    assessorValue: sys.assessor && sys.assessor.value,
    assessorYear: sys.assessor && sys.assessor.year,
    rebuildValue: sys.replacementCost && sys.replacementCost.value,
    arvValue: sys.arv && sys.arv.value,
    beds: prop.bedrooms, baths: prop.bathrooms,
    sqft: prop.squareFootage, yearBuilt: prop.yearBuilt,
    comps: Array.isArray(r && r.cma && r.cma.sold) && r.cma.sold.length
      ? r.cma.sold.slice(0, 5).map((s) => ({ address: s.address, sqft: s.squareFootage, price: s.soldPrice, daysOld: s.soldDate ? null : null, soldDate: s.soldDate }))
      : (Array.isArray(r && r.comps) ? r.comps.slice(0, 5).map((c) => ({ address: c.formattedAddress, sqft: c.squareFootage, price: c.price, daysOld: c.daysOld })) : []),
    soldCount: stats.soldCount,
    soldMedian: stats.soldMedian,
    soldWindowMonths: stats.soldWindowMonths,
    moi: stats.monthsOfInventory,
    lean: stats.marketLean,
    rentMonthly: inv.monthlyRent,
    capRate: inv.capRate
  };
}

export function renderValuationReport(d) {
  d = d || {};
  const street = String(d.street || (d.formatted ? String(d.formatted).split(",")[0] : "") || "").trim();
  const label = street || "your home";
  const trueV = money(d.trueValue) || money(d.avmValue);

  const rows = [];
  const sysRow = (name, val, note) => {
    if (!val) return;
    rows.push(
      '<tr><td class="dz-muted" style="padding:8px 16px 8px 0;font-family:' + FONT + ';font-size:12px;letter-spacing:0.6px;text-transform:uppercase;color:#757575;white-space:nowrap;vertical-align:top;">' + name + '</td>' +
      '<td class="dz-p" style="padding:8px 0;font-family:' + FONT + ';font-size:16px;font-weight:700;color:#2b2b2b;text-align:right;white-space:nowrap;">' + val +
      (note ? ' <span class="dz-muted" style="font-weight:400;font-size:12px;color:#757575;">' + note + '</span>' : "") + '</td></tr>'
    );
  };
  sysRow("Market model", money(d.avmValue), "");
  sysRow("County assessor", money(d.assessorValue), d.assessorYear ? "(" + escapeHtml(String(d.assessorYear)) + ")" : "");
  sysRow("Rebuild cost", money(d.rebuildValue), "");
  sysRow("Renovated ceiling", money(d.arvValue), "");

  const facts = [
    d.beds ? d.beds + " bd" : "",
    d.baths ? d.baths + " ba" : "",
    d.sqft ? Number(d.sqft).toLocaleString("en-US") + " sqft" : "",
    d.yearBuilt ? "built " + d.yearBuilt : ""
  ].filter(Boolean).join(" &nbsp;&middot;&nbsp; ");

  let compsHtml = "";
  const comps = (d.comps || []).filter((c) => c && c.address && money(c.price));
  if (comps.length) {
    const th = (txt, right) =>
      '<td class="dz-muted" style="padding:0 0 6px' + (right ? ";text-align:right" : "") + ';font-family:' + FONT + ';font-size:11px;letter-spacing:0.8px;text-transform:uppercase;color:#757575;">' + txt + '</td>';
    const compRows = comps.map((c) =>
      '<tr>' +
      '<td class="dz-p" style="padding:6px 12px 6px 0;font-family:' + FONT + ';font-size:14px;color:#2b2b2b;">' + escapeHtml(String(c.address).split(",")[0]) +
      (c.sqft ? ' <span class="dz-muted" style="font-size:12px;color:#757575;">' + Number(c.sqft).toLocaleString("en-US") + ' sqft</span>' : "") + '</td>' +
      '<td class="dz-p" style="padding:6px 0;font-family:' + FONT + ';font-size:14px;font-weight:700;color:#2b2b2b;text-align:right;white-space:nowrap;">' + money(c.price) +
      (ago(c.daysOld) ? ' <span class="dz-muted" style="font-weight:400;font-size:12px;color:#757575;">' + ago(c.daysOld) + '</span>' : "") + '</td>' +
      '</tr>'
    ).join("");
    compsHtml =
      '<p class="dz-muted" style="margin:26px 0 8px;font-family:' + FONT + ';font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#d9222a;">What actually sold nearby</p>' +
      '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width:100%;">' +
      '<tr>' + th("Sold comp") + th("Closed for", true) + '</tr>' + compRows + '</table>';
  }

  const marketBits = [];
  if (d.soldCount && d.soldMedian) {
    marketBits.push(d.soldCount + " similar " + (d.soldCount === 1 ? "home" : "homes") + " closed nearby in the last " + (d.soldWindowMonths || 9) + " months, median " + money(d.soldMedian));
  }
  if (d.moi != null) {
    marketBits.push(d.moi + " months of inventory" + (d.lean ? " (" + escapeHtml(String(d.lean)) + "'s market)" : ""));
  }
  if (d.rentMonthly) {
    marketBits.push("investor read: rents about " + money(d.rentMonthly) + "/mo" + (d.capRate != null ? " at a " + d.capRate + "% cap" : ""));
  }
  const marketHtml = marketBits.length
    ? '<p class="dz-p" style="margin:22px 0 0;font-family:' + FONT + ';font-size:14px;line-height:1.65;color:#2b2b2b;">' + escapeHtml(marketBits.join(". ").replace(/&#?\w+;/g, (m) => m)) + '.</p>'
    : "";

  const range = (money(d.avmLow) && money(d.avmHigh))
    ? '<p class="dz-muted" style="margin:6px 0 0;font-family:' + FONT + ';font-size:13px;color:#757575;">Confidence range ' + money(d.avmLow) + ' to ' + money(d.avmHigh) + '</p>'
    : "";

  const bodyHtml =
    '<p class="dz-p" style="margin:0 0 20px;font-family:' + FONT + ';font-size:16px;line-height:1.65;color:#2b2b2b;">Here is the instant read on <strong>' + escapeHtml(label) + '</strong>, straight from my valuation model. My thorough CMA, built by hand, follows right behind it.</p>' +
    (trueV
      ? '<div style="text-align:center;padding:22px 0 24px;">' +
        '<p class="dz-muted" style="margin:0 0 6px;font-family:' + FONT + ';font-size:11px;font-weight:700;letter-spacing:1.6px;text-transform:uppercase;color:#d9222a;">True market value</p>' +
        '<p class="dz-h" style="margin:0;font-family:' + FONT + ';font-size:42px;line-height:1.1;font-weight:800;letter-spacing:-1px;color:#1a1816;">' + trueV + '</p>' +
        range +
        '<p class="dz-muted" style="margin:8px 0 0;font-family:' + FONT + ';font-size:13px;color:#757575;">The number I would defend to a buyer.</p>' +
        '</div>'
      : "") +
    (rows.length
      ? '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-top:1px solid #ece7e1;margin-top:4px;">' + rows.join("") + '</table>'
      : "") +
    (facts ? '<p class="dz-muted" style="margin:14px 0 0;font-family:' + FONT + ';font-size:13px;color:#757575;">' + facts + '</p>' : "") +
    compsHtml +
    marketHtml +
    '<p class="dz-p" style="margin:24px 0 0;font-family:' + FONT + ';font-size:15px;line-height:1.65;color:#2b2b2b;">These are model numbers on today\'s data. The CMA I build by hand walks the same street with human eyes, and it is already in motion. Want it faster, or want me to walk the home itself? Call or text me directly.</p>';

  const textLines = [
    "Instant valuation: " + (street || d.formatted || "your home"),
    "",
    trueV ? "TRUE MARKET VALUE: " + trueV : "",
    (money(d.avmLow) && money(d.avmHigh)) ? "Confidence range: " + money(d.avmLow) + " - " + money(d.avmHigh) : "",
    money(d.avmValue) ? "Market model: " + money(d.avmValue) : "",
    money(d.assessorValue) ? "County assessor: " + money(d.assessorValue) + (d.assessorYear ? " (" + d.assessorYear + ")" : "") : "",
    money(d.rebuildValue) ? "Rebuild cost: " + money(d.rebuildValue) : "",
    money(d.arvValue) ? "Renovated ceiling: " + money(d.arvValue) : "",
    "",
    comps.length ? "Sold nearby:" : "",
    ...comps.map((c) => "  " + String(c.address).split(",")[0] + " - " + money(c.price) + (ago(c.daysOld) ? " (" + ago(c.daysOld) + ")" : "")),
    "",
    "My thorough CMA, built by hand, follows right behind this.",
    "Call or text: (949) 438-5948",
    "",
    "Joshua Guerrero",
    "Active Realty, California DRE #02267255"
  ].filter((l) => l !== "");

  return {
    subject: street ? street + ": your instant valuation" : "Your instant home valuation",
    html: renderEmail({
      subject: street ? street + ": your instant valuation" : "Your instant home valuation",
      preheader: "True market value, the comps behind it, and the investor read. Your hand-built CMA follows.",
      headline: escapeHtml(street ? "What " + street + " is worth" : "What your home is worth"),
      bodyHtml,
      ctaLabel: "Call or text (949) 438-5948",
      ctaUrl: "tel:+19494385948",
      signature: true,
      unsubUrl: "",
      pixelUrl: "",
      postal: ""
    }),
    text: textLines.join("\n")
  };
}
