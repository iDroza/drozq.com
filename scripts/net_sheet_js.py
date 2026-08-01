"""The /net-sheet/ client engine + JSON-LD.

Split out of build_net_sheet.py purely for file size. Everything the calculator
does runs client-side so the tool works with or without a county lookup: the
API supplies data, this supplies the math.
"""

JS = r"""<script id="ns-js">
(function(){
  "use strict";
  var $ = function(id){ return document.getElementById(id); };
  if (!$("ns-price")) return;

  /* ---------------- tax tables (2026) ---------------------------------- */
  /* Federal long-term capital gains, Rev. Proc. 2025-32. NIIT is the 3.8%
     net investment income tax over the MAGI threshold. */
  var FED = {
    single: { t0: 49450, t15: 545500, niit: 200000 },
    mfj:    { t0: 98900, t15: 613700, niit: 250000 }
  };
  /* California taxes capital gain as ordinary income. Joint thresholds are
     exactly double the single ones (R&TC 17041). The 1% behavioral health
     surcharge sits at $1,000,000 for every filing status. */
  var CA_BRACKETS = [[0,.01],[10756,.02],[25499,.04],[40245,.06],[55866,.08],[70606,.093],[360659,.103],[432787,.113],[721314,.123]];

  /* ---------------- helpers -------------------------------------------- */
  function num(el){ if(!el) return 0; var v = parseFloat(String(el.value||"").replace(/[^0-9.\-]/g,"")); return isFinite(v) ? v : 0; }
  function money(n){ var r = Math.round(n||0); return "$" + Math.abs(r).toLocaleString("en-US"); }
  function signed(n){ var r = Math.round(n||0); if (r === 0) return "$0"; return (r < 0 ? "−" : "+") + "$" + Math.abs(r).toLocaleString("en-US"); }
  function minus(n){ var r = Math.round(n||0); return r === 0 ? "$0" : "−$" + Math.abs(r).toLocaleString("en-US"); }
  function esc(s){ return String(s==null?"":s).replace(/[&<>"']/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]; }); }
  function setText(id, t){ var el = $(id); if (el) el.textContent = t; }
  function setVal(id, v){ var el = $(id); if (el) el.value = (v||v===0) ? Math.round(v).toLocaleString("en-US") : "0"; }
  function pDate(s){ var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s||"")); return m ? new Date(+m[1], +m[2]-1, +m[3]) : null; }
  function pad2(n){ return (n < 10 ? "0" : "") + n; }
  function iso(d){ return d.getFullYear() + "-" + pad2(d.getMonth()+1) + "-" + pad2(d.getDate()); }
  function monthsBetween(a, b){ return (b.getFullYear()-a.getFullYear())*12 + (b.getMonth()-a.getMonth()) + (b.getDate() >= a.getDate() ? 0 : -1); }
  function fmtDate(s){ var d = pDate(s); if (!d) return String(s||""); return d.toLocaleDateString("en-US",{month:"short", day:"numeric", year:"numeric"}); }

  function track(ev, props){
    try { if (window.posthog && posthog.capture) posthog.capture(ev, props||{}); } catch(e){}
    try {
      window.dataLayer = window.dataLayer || [];
      var p = { event: ev }, src = props || {};
      for (var k in src) { if (Object.prototype.hasOwnProperty.call(src, k)) p[k] = src[k]; }
      window.dataLayer.push(p);
    } catch(e){}
  }
  var usedOnce = false;
  function markUsed(){ if (usedOnce) return; usedOnce = true; track("net_sheet_calc_used", {}); }

  /* ---------------- shared state --------------------------------------- */
  var RECORD = null;                       /* the county pull, once it lands */
  var cityRule = { kind: "none" };         /* city transfer tax rule         */
  var lastAddress = "";

  /* ---------------- city transfer tax ----------------------------------
     kind "flat"    -> rate on the full price
     kind "tiered"  -> first bracket whose min the price meets, on the full price
     kind "stacked" -> base rate on the full price, plus a bracket rate on the
                       full price once the price clears a threshold (LA + ULA) */
  function cityTransferTax(price){
    if (!cityRule || !price) return 0;
    if (cityRule.kind === "flat")   return price * (cityRule.rate || 0);
    if (cityRule.kind === "tiered") {
      var tiers = cityRule.tiers || [];
      for (var i = 0; i < tiers.length; i++) { if (price >= tiers[i].min) return price * tiers[i].rate; }
      return 0;
    }
    if (cityRule.kind === "stacked") {
      var t = price * (cityRule.base || 0), ts = cityRule.tiers || [];
      for (var j = 0; j < ts.length; j++) { if (price >= ts[j].min) { t += price * ts[j].rate; break; } }
      return t;
    }
    return 0;
  }

  /* ---------------- property tax proration -----------------------------
     California fiscal year: July 1 to June 30, billed in two installments
     (Jul-Dec due Nov 1, Jan-Jun due Feb 1). Escrow charges the seller for
     every day owned in the fiscal year and compares that against what was
     already paid. 30/360 day convention, the escrow standard. */
  function prorateTax(annual, closeISO, inst1, inst2){
    var d = pDate(closeISO);
    if (!d || !(annual > 0)) return { line: 0, days: 0, share: 0, paid: 0, fy: null };
    var y = d.getFullYear(), m = d.getMonth() + 1, day = Math.min(d.getDate(), 30);
    var fy = (m >= 7) ? y : y - 1;
    var monthsIn = ((y - fy) * 12) + (m - 7);
    var days = Math.max(0, Math.min(360, monthsIn * 30 + (day - 1)));
    var share = annual * days / 360;
    var paid = (inst1 ? annual/2 : 0) + (inst2 ? annual/2 : 0);
    return { line: paid - share, days: days, share: share, paid: paid, fy: fy };
  }

  /* HOA dues are paid at the start of the month for that month, so the seller
     is credited for the part of the month the buyer owns. */
  function prorateHOA(monthly, closeISO){
    var d = pDate(closeISO);
    if (!d || !(monthly > 0)) return 0;
    var owned = Math.min(Math.max(d.getDate() - 1, 0), 30);
    return monthly * (30 - owned) / 30;
  }

  /* ---------------- amortization --------------------------------------- */
  function payment(P, i, n){ return (i <= 0) ? P/n : P * i / (1 - Math.pow(1+i, -n)); }
  /* Exactly one monthly rate satisfies (principal, term, payment). Bisect it. */
  function solveRate(P, M, n){
    if (!(P > 0 && M > 0 && n > 0)) return null;
    if (M * n <= P) return null;                     /* never amortizes       */
    var lo = 1e-9, hi = 0.02;                        /* 0 to ~24% APR         */
    if (payment(P, hi, n) < M) return null;          /* payment above the top */
    for (var k = 0; k < 200; k++){ var mid = (lo+hi)/2; if (payment(P, mid, n) < M) lo = mid; else hi = mid; }
    return (lo + hi) / 2;
  }
  function balanceAfter(P, i, M, k){
    if (k <= 0) return P;
    if (i <= 0) return Math.max(0, P - M * k);
    var g = Math.pow(1+i, k);
    return Math.max(0, P * g - M * (g - 1) / i);
  }

  /* ---------------- capital gains -------------------------------------- */
  function caTax(income, filing){
    if (!(income > 0)) return 0;
    var mult = (filing === "mfj") ? 2 : 1, t = 0;
    for (var i = 0; i < CA_BRACKETS.length; i++){
      var lo = CA_BRACKETS[i][0] * mult;
      var hi = (i+1 < CA_BRACKETS.length) ? CA_BRACKETS[i+1][0] * mult : Infinity;
      if (income > lo) t += (Math.min(income, hi) - lo) * CA_BRACKETS[i][1];
    }
    if (income > 1000000) t += (income - 1000000) * 0.01;
    return t;
  }
  function fedLTCG(gain, other, filing){
    var f = FED[filing] || FED.mfj;
    var base = Math.max(0, other), top = base + gain;
    var at15 = Math.max(0, Math.min(top, f.t15) - Math.max(base, f.t0));
    var at20 = Math.max(0, top - Math.max(base, f.t15));
    var at0  = Math.max(0, Math.min(top, f.t0) - base);
    var niit = Math.min(gain, Math.max(0, top - f.niit)) * 0.038;
    return { tax: at15*0.15 + at20*0.20, niit: niit, at0: at0, at15: at15, at20: at20 };
  }

  /* ---------------- payoff modes --------------------------------------- */
  var payoffMode = "known";
  var solvedPayoff = 0, solvedRate = null;

  function setMode(mode){
    payoffMode = mode;
    var btns = document.querySelectorAll('.ns-seg button[data-mode]');
    for (var i = 0; i < btns.length; i++) btns[i].setAttribute("aria-pressed", btns[i].getAttribute("data-mode") === mode ? "true" : "false");
    var modes = ["known","payment","terms"];
    for (var m = 0; m < modes.length; m++){
      var el = $("ns-mode-" + modes[m]);
      if (el) el.classList.toggle("is-on", modes[m] === mode);
    }
    recalc();
  }
  var segBtns = document.querySelectorAll('.ns-seg button[data-mode]');
  for (var si = 0; si < segBtns.length; si++){
    segBtns[si].addEventListener("click", function(){ setMode(this.getAttribute("data-mode")); markUsed(); });
  }

  function computePayoff(closeISO){
    if (payoffMode === "known") { solvedRate = null; return num($("ns-payoff")); }

    var close = pDate(closeISO) || new Date();
    if (payoffMode === "payment"){
      var P = num($("ns-p-orig")), pay = num($("ns-p-pay")), n = parseInt(($("ns-p-term")||{}).value || "360", 10);
      var start = pDate(($("ns-p-start")||{}).value);
      var piti = !!($("ns-p-piti")||{}).checked;
      var pi = pay, stripped = 0;
      if (piti){
        stripped = (num($("ns-tax-annual")) / 12) + num($("ns-p-ins")) + num($("ns-p-pmi")) + num($("ns-hoa-monthly"));
        pi = pay - stripped;
      }
      var out = $("ns-solve-out");
      if (!(P > 0) || !(pi > 0) || !start){
        if (out) out.innerHTML = "<p>Fill in the loan amount, start date, and payment.</p>";
        solvedRate = null; solvedPayoff = 0; return 0;
      }
      var i = solveRate(P, pi, n);
      if (i == null){
        if (out) out.innerHTML = '<p class="ns-warn">That payment does not amortize that loan over that term.</p>' +
          "<p>Check whether the payment includes taxes and insurance, and whether the loan amount and term are right.</p>";
        solvedRate = null; solvedPayoff = 0; return 0;
      }
      var k = Math.max(0, Math.min(n, monthsBetween(start, close) + 1));
      var bal = balanceAfter(P, i, pi, k);
      solvedRate = i * 12 * 100;
      solvedPayoff = bal;
      if (out){
        out.innerHTML =
          "<p>Solved rate: <b>" + solvedRate.toFixed(3) + "%</b> on a " + (n/12) + "-year loan.</p>" +
          "<p>Principal and interest: <b>" + money(pi) + "</b>" +
            (piti && stripped > 0 ? " (after removing " + money(stripped) + " of taxes, insurance, and dues)" : "") + "</p>" +
          "<p>Payments made by close: <b>" + k + "</b> of " + n + ". Principal paid down: <b>" + money(P - bal) + "</b>.</p>" +
          "<p>Estimated balance at close: <b>" + money(bal) + "</b></p>";
      }
      return bal;
    }

    /* mode: terms */
    var Pt = num($("ns-t-orig")), rate = num($("ns-t-rate")) / 100 / 12;
    var nt = parseInt(($("ns-t-term")||{}).value || "360", 10);
    var st = pDate(($("ns-t-start")||{}).value);
    var to = $("ns-terms-out");
    if (!(Pt > 0) || !(rate > 0) || !st){
      if (to) to.innerHTML = "<p>Fill in the loan amount, rate, and start date.</p>";
      solvedRate = null; solvedPayoff = 0; return 0;
    }
    var pmt = payment(Pt, rate, nt);
    var kt = Math.max(0, Math.min(nt, monthsBetween(st, close) + 1));
    var bt = balanceAfter(Pt, rate, pmt, kt);
    solvedRate = rate * 12 * 100;
    solvedPayoff = bt;
    if (to){
      to.innerHTML =
        "<p>Principal and interest: <b>" + money(pmt) + "</b> a month.</p>" +
        "<p>Payments made by close: <b>" + kt + "</b> of " + nt + ". Principal paid down: <b>" + money(Pt - bt) + "</b>.</p>" +
        "<p>Estimated balance at close: <b>" + money(bt) + "</b></p>";
    }
    return bt;
  }

  /* Payoff charges: interest to the wire date plus the lender's fees. Only
     auto-filled while the seller has not typed their own number. */
  var extraTouched = false;
  function autoPayoffExtras(balance){
    if (extraTouched) return num($("ns-payoff-extra"));
    var r = (solvedRate != null) ? solvedRate/100 : 0.055;
    var est = (balance > 0) ? (balance * r / 365 * 12) + 155 : 0;   /* ~12 days + reconveyance/statement/wire */
    setVal("ns-payoff-extra", est);
    return est;
  }

  /* ---------------- the net sheet -------------------------------------- */
  function recalc(){
    var P = num($("ns-price"));
    var closeISO = ($("ns-close")||{}).value || "";

    /* city transfer tax tracks the price whenever we know the rule */
    if (cityRule && cityRule.kind && cityRule.kind !== "none") setVal("ns-tt-city", cityTransferTax(P));

    var comm = P * (num($("ns-comm-l")) + num($("ns-comm-b"))) / 100;
    var closing = num($("ns-escrow")) + num($("ns-title")) + num($("ns-tt-county")) + num($("ns-tt-city")) + num($("ns-misc"));
    var items = num($("ns-nhd")) + num($("ns-warranty")) + num($("ns-termite")) + num($("ns-termite-work")) +
                num($("ns-hoa-fees")) + num($("ns-retrofit")) + num($("ns-prep")) + num($("ns-concessions"));

    var pr = prorateTax(num($("ns-tax-annual")), closeISO, ($("ns-inst1")||{}).checked, ($("ns-inst2")||{}).checked);
    var hoaPro = prorateHOA(num($("ns-hoa-monthly")), closeISO);

    var proOut = $("ns-pro-out");
    if (proOut){
      if (pr.fy == null && !(hoaPro > 0)){
        proOut.innerHTML = "<p>Enter an annual tax bill to see the proration.</p>";
      } else {
        var h = "";
        if (pr.fy != null){
          h += "<p>Fiscal year <b>" + pr.fy + "-" + (pr.fy+1) + "</b>. You own it for <b>" + pr.days +
               "</b> of 360 days, a share of <b>" + money(pr.share) + "</b>.</p>";
          h += "<p>Paid so far: <b>" + money(pr.paid) + "</b>. " + (pr.line >= 0
            ? "The buyer reimburses you <b>" + money(pr.line) + "</b>."
            : "You are debited <b>" + money(-pr.line) + "</b> at close.") + "</p>";
        }
        if (hoaPro > 0) h += "<p>HOA dues credited back to you: <b>" + money(hoaPro) + "</b>.</p>";
        proOut.innerHTML = h;
      }
    }

    var balance = computePayoff(closeISO);
    if (payoffMode !== "known") setVal("ns-payoff", balance);
    var extras = autoPayoffExtras(balance);
    var payoffTotal = balance + num($("ns-payoff2")) + extras;

    var withheld = (($("ns-593")||{}).checked ? P * 0.0333333 : 0) + (($("ns-firpta")||{}).checked ? P * 0.15 : 0);

    var netBeforePayoff = P - comm - closing - items + pr.line + hoaPro;
    var cash = netBeforePayoff - payoffTotal - withheld;
    var costOfSale = P - netBeforePayoff;

    /* capital gains */
    var cgOn = !!($("ns-cg-on")||{}).checked, cgTotal = 0;
    var cgFields = $("ns-cg-fields");
    if (cgFields) cgFields.classList.toggle("is-on", cgOn);
    if (cgOn){
      var filing = ($("ns-cg-filing")||{}).value || "mfj";
      var sellingCosts = comm + closing + items;
      var basis = num($("ns-cg-basis")) + num($("ns-cg-improve"));
      var gain = (P - sellingCosts) - basis;
      var excl = ($("ns-cg-primary")||{}).checked ? (filing === "mfj" ? 500000 : 250000) : 0;
      var taxable = Math.max(0, gain - excl);
      var other = num($("ns-cg-income"));
      var fed = fedLTCG(taxable, other, filing);
      var ca = caTax(other + taxable, filing) - caTax(other, filing);
      cgTotal = fed.tax + fed.niit + ca;
      var cgOut = $("ns-cg-out");
      if (cgOut){
        cgOut.innerHTML =
          "<p>Amount realized: <b>" + money(P - sellingCosts) + "</b> (price less " + money(sellingCosts) + " of selling costs).</p>" +
          "<p>Adjusted basis: <b>" + money(basis) + "</b>. Gain: <b>" + money(gain) + "</b>.</p>" +
          "<p>Exclusion applied: <b>" + money(excl) + "</b>. Taxable gain: <b>" + money(taxable) + "</b>.</p>" +
          (taxable > 0
            ? "<p>Federal capital gains: <b>" + money(fed.tax) + "</b>" +
              (fed.niit > 0 ? " plus <b>" + money(fed.niit) + "</b> net investment income tax" : "") +
              ". California, as ordinary income: <b>" + money(ca) + "</b>.</p>" +
              "<p>Estimated total: <b>" + money(cgTotal) + "</b></p>"
            : "<p><b>The exclusion covers the whole gain.</b> No capital gains tax estimated on this sale.</p>");
      }
    }

    /* ---- paint ---- */
    setText("ns-o-price", money(P));
    setText("ns-o-comm", minus(comm));      setText("ns-o-comm-h", minus(comm));
    setText("ns-o-close", minus(closing));  setText("ns-o-close-h", minus(closing));
    setText("ns-o-items", minus(items));    setText("ns-o-items-h", minus(items));
    setText("ns-o-tax", signed(pr.line));
    setText("ns-o-hoa", signed(hoaPro));
    setText("ns-o-pro-h", signed(pr.line + hoaPro));
    setText("ns-o-cos", minus(costOfSale));
    setText("ns-o-payoff", minus(payoffTotal));  setText("ns-o-payoff-h", minus(payoffTotal));
    setText("ns-o-wh-h", withheld > 0 ? minus(withheld) : "$0");

    var whRow = $("ns-o-wh-row");
    if (whRow){ whRow.style.display = withheld > 0 ? "" : "none"; setText("ns-o-wh", minus(withheld)); }

    var netEl = $("ns-o-net");
    if (netEl){
      netEl.textContent = (cash < 0 ? "−" : "") + money(cash);
      netEl.className = cash < 0 ? "ns-neg" : "";
    }
    var pctEl = $("ns-o-pct");
    if (pctEl){
      var pct = P > 0 ? (costOfSale / P * 100) : 0;
      pctEl.textContent = "Cost of sale: " + money(costOfSale) + ", " + pct.toFixed(1) + "% of the sale price." +
        (withheld > 0 ? " " + money(withheld) + " of that is withholding, credited back when you file." : "");
    }

    var after = $("ns-after");
    if (after){
      after.style.display = (cgOn && cgTotal > 0) ? "" : "none";
      if (cgOn && cgTotal > 0){
        setText("ns-o-cg", minus(cgTotal));
        setText("ns-o-aftertax", money(netBeforePayoff - payoffTotal - cgTotal));
      }
    }
    setText("ns-o-cg-h", (cgOn && cgTotal > 0) ? minus(cgTotal) : "$0");

    scheduleFit();
  }

  /* ---------------- wiring --------------------------------------------- */
  var MONEY_IDS = ["ns-price","ns-escrow","ns-title","ns-tt-county","ns-tt-city","ns-misc","ns-nhd","ns-warranty",
    "ns-termite","ns-termite-work","ns-hoa-fees","ns-retrofit","ns-prep","ns-concessions","ns-tax-annual",
    "ns-hoa-monthly","ns-payoff","ns-payoff2","ns-payoff-extra","ns-p-orig","ns-p-pay","ns-p-ins","ns-p-pmi",
    "ns-t-orig","ns-cg-basis","ns-cg-improve","ns-cg-income"];
  var PLAIN_IDS = ["ns-comm-l","ns-comm-b","ns-t-rate"];
  var OTHER_IDS = ["ns-inst1","ns-inst2","ns-p-start","ns-p-term","ns-p-piti","ns-t-term","ns-t-start",
    "ns-593","ns-firpta","ns-cg-on","ns-cg-filing","ns-cg-primary"];

  MONEY_IDS.concat(PLAIN_IDS).forEach(function(id){
    var el = $(id); if (!el) return;
    var isMoney = MONEY_IDS.indexOf(id) >= 0;
    el.addEventListener("input", function(){ markUsed(); recalc(); });
    el.addEventListener("blur", function(){
      if (isMoney){ var v = num(el); el.value = v ? Math.round(v).toLocaleString("en-US") : "0"; }
      recalc();
    });
  });
  OTHER_IDS.forEach(function(id){
    var el = $(id); if (!el) return;
    el.addEventListener("change", function(){ markUsed(); recalc(); });
  });
  var extraEl = $("ns-payoff-extra");
  if (extraEl) extraEl.addEventListener("input", function(){ extraTouched = true; });

  var pitiBox = $("ns-p-piti");
  if (pitiBox) pitiBox.addEventListener("change", function(){
    var f = $("ns-p-piti-fields"); if (f) f.style.display = this.checked ? "block" : "none";
  });

  var moreBtn = $("ns-payoff-more");
  if (moreBtn) moreBtn.addEventListener("click", function(){
    var adv = $("ns-payoff-adv"), on = !adv.classList.contains("is-on");
    adv.classList.toggle("is-on", on);
    this.setAttribute("aria-expanded", on ? "true" : "false");
  });

  /* The output card never scrolls inside itself. It sticks while it fits under
     the fixed header; the moment its content is taller than the viewport
     (short laptop, or the capital gains rows opening) it drops to static and
     scrolls with the page, so the whole card is always readable. */
  function fitOut(){
    var out = $("ns-out");
    if (!out) return;
    out.classList.remove("ns-out--tall");
    if (window.innerWidth >= 992 && out.offsetHeight + 108 > window.innerHeight) out.classList.add("ns-out--tall");
  }
  var fitRaf = null;
  function scheduleFit(){
    if (fitRaf) return;
    fitRaf = requestAnimationFrame(function(){ fitRaf = null; fitOut(); });
  }
  window.addEventListener("resize", scheduleFit);

  var printBtn = $("ns-print");
  if (printBtn) printBtn.addEventListener("click", function(){ track("net_sheet_print", {}); window.print(); });

  var ctaBtn = $("ns-cta");
  if (ctaBtn) ctaBtn.addEventListener("click", function(){
    track("net_sheet_cta", { has_record: !!RECORD });
    if (typeof window.openFunnel === "function") window.openFunnel(lastAddress || "", "sell");
  });

  /* Defaults: close 45 days out, with the installment toggles set the way the
     tax collector's calendar implies for that date. */
  function seedInstallments(){
    var d = pDate(($("ns-close")||{}).value); if (!d) return;
    var y = d.getFullYear(), m = d.getMonth() + 1;
    var fy = (m >= 7) ? y : y - 1;
    var b1 = $("ns-inst1"), b2 = $("ns-inst2");
    if (b1) b1.checked = d >= new Date(fy, 10, 10);      /* Nov 10 */
    if (b2) b2.checked = d >= new Date(fy + 1, 1, 10);   /* Feb 10 */
  }
  (function seedDates(){
    var d = new Date(); d.setDate(d.getDate() + 45);
    var el = $("ns-close");
    if (el && !el.value) el.value = iso(d);
    seedInstallments();
  })();
  var closeEl = $("ns-close");
  if (closeEl) closeEl.addEventListener("change", function(){ markUsed(); seedInstallments(); recalc(); });

  /* ---------------- Places on the bespoke lookup input ------------------
     This input has its OWN Autocomplete, so it carries its own copy of the
     homepage "input-pill-flattens" pattern (TEMPLATE.md section 4): snap the
     dropdown flush to the input and flatten the pill's bottom corners while
     it is open. Once a synced landing pill has been focused, cede position to
     the synced aligner so the two never ping-pong over the same dropdown. */
  var addrInput = $("ns-address"), selectedPlace = null;
  function waitForMaps(cb, tries){
    tries = tries || 0;
    if (window.google && google.maps && google.maps.places && google.maps.places.Autocomplete) { cb(); return; }
    if (tries > 120) return;
    setTimeout(function(){ waitForMaps(cb, tries + 1); }, 100);
  }
  waitForMaps(function bindPlaces(){
    if (!addrInput || !window.google) return;
    try {
      var ac = new google.maps.places.Autocomplete(addrInput, {
        types: ["address"], componentRestrictions: { country: "us" },
        fields: ["address_components","formatted_address","geometry","place_id"]
      });
      ac.addListener("place_changed", function(){
        var p = ac.getPlace();
        if (p && p.geometry) selectedPlace = p;
      });
      var pill = $("ns-pill"), pacActive = false, observer = null, raf = null, syncedArmed = false;
      var landing = document.querySelectorAll('form.pos_relative input[name="location"]');
      for (var li = 0; li < landing.length; li++) landing[li].addEventListener("focus", function(){ syncedArmed = true; }, true);
      function align(){
        if (!pacActive || !pill) return;
        var pacs = document.querySelectorAll(".pac-container");
        if (!pacs.length) return;
        var r = addrInput.getBoundingClientRect();
        var L = (r.left + window.scrollX) + "px", T = (r.bottom + window.scrollY) + "px", W = r.width + "px", any = false;
        for (var i = 0; i < pacs.length; i++){
          if (pacs[i].style.display === "none") continue;
          any = true;
          if (!syncedArmed){
            if (pacs[i].style.left !== L) pacs[i].style.left = L;
            if (pacs[i].style.top !== T) pacs[i].style.top = T;
            if (pacs[i].style.width !== W) pacs[i].style.width = W;
          }
        }
        pill.classList.toggle("is-pac-open", any);
      }
      function ensureObserver(){
        if (observer) return;
        var pacs = document.querySelectorAll(".pac-container");
        if (!pacs.length) return;
        observer = new MutationObserver(align);
        for (var i = 0; i < pacs.length; i++) observer.observe(pacs[i], { attributes: true, attributeFilter: ["style"] });
      }
      function schedule(){ if (raf) return; raf = requestAnimationFrame(function(){ raf = null; align(); }); }
      addrInput.addEventListener("focus", function(){ pacActive = true; setTimeout(function(){ ensureObserver(); align(); }, 0); });
      addrInput.addEventListener("input", function(){ selectedPlace = null; schedule(); });
      addrInput.addEventListener("blur", function(){ setTimeout(function(){ pacActive = false; if (pill) pill.classList.remove("is-pac-open"); }, 150); });
      window.addEventListener("resize", schedule);
      window.addEventListener("scroll", schedule, true);
    } catch(e){}
  });

  /* ---------------- lookup + gate --------------------------------------
     Gate FIRST: submitting the address opens the contact dialog and fetches
     nothing. /api/netsheet refuses to compute or return the county record
     without email + phone + consent, so the record never enters the browser
     un-gated, and pulling it always saves the lead. */
  var lookupForm = $("ns-lookup-form"), lookupErr = $("ns-lookup-err");
  var gate = $("ns-gate"), gateForm = $("ns-gate-form"), gateName = $("ns-gate-name"), gateEmail = $("ns-gate-email"),
      gatePhone = $("ns-gate-phone"), gateErr = $("ns-gate-error"), gateClose = $("ns-gate-close"),
      gateSubmit = $("ns-gate-submit"), gateAddr = $("ns-gate-address");
  var pending = { address: "", lat: null, lng: null }, gateOpen = false, generating = false;

  function showLookupError(msg){ if (lookupErr){ lookupErr.textContent = msg; lookupErr.classList.add("is-shown"); } }
  function clearLookupError(){ if (lookupErr){ lookupErr.textContent = ""; lookupErr.classList.remove("is-shown"); } }

  /* Mirrors the funnel's normalizeUsDigits: drop a leaked +1, then cap at 10.
     NANP area codes never start with 1, so a leading 1 on 11 digits is always
     the country code (the Mary Morris fix). */
  function digits(v){ var d = String(v==null?"":v).replace(/\D/g,""); while (d.length > 10 && d.charAt(0) === "1") d = d.slice(1); return d.slice(0,10); }
  if (gatePhone) gatePhone.addEventListener("input", function(){
    var d = digits(this.value), out = "";
    if (d.length > 0) out = "(" + d.slice(0,3);
    if (d.length >= 4) out += ") " + d.slice(3,6);
    if (d.length >= 7) out += "-" + d.slice(6,10);
    this.value = out;
  });

  function clearGateError(){
    if (gateErr){ gateErr.textContent = ""; gateErr.classList.remove("is-shown"); }
    [gateName, gateEmail, gatePhone].forEach(function(el){ if (el) el.classList.remove("is-error"); });
  }
  function showGateError(msg, el){
    if (gateErr){ gateErr.textContent = msg; gateErr.classList.add("is-shown"); }
    if (el){ el.classList.add("is-error"); try { el.focus(); } catch(e){} }
  }

  function openGate(address, lat, lng){
    pending = { address: address || "", lat: (lat != null ? lat : null), lng: (lng != null ? lng : null) };
    if (gateAddr) gateAddr.textContent = pending.address || "your home";
    if (!gate) return;
    clearGateError();
    gate.classList.add("is-open");
    gate.setAttribute("aria-hidden","false");
    gateOpen = true;
    try { document.documentElement.style.overflow = "hidden"; document.body.style.overflow = "hidden"; } catch(e){}
    document.addEventListener("keydown", onGateKey);
    setTimeout(function(){ try { if (gateName) gateName.focus(); } catch(e){} }, 60);
    track("net_sheet_gate_shown", { address: pending.address });
  }
  function hideGate(){
    if (gate){ gate.classList.remove("is-open"); gate.setAttribute("aria-hidden","true"); }
    gateOpen = false;
    try { document.documentElement.style.overflow = ""; document.body.style.overflow = ""; } catch(e){}
    document.removeEventListener("keydown", onGateKey);
  }
  function abandonGate(method){
    if (!gateOpen || generating) return;
    track("net_sheet_gate_dismiss", { address: pending.address, method: method || "close" });
    hideGate();
  }
  function onGateKey(e){ if (e.key === "Escape" || e.keyCode === 27) abandonGate("esc"); }
  if (gateClose) gateClose.addEventListener("click", function(){ abandonGate("close"); });

  if (lookupForm) lookupForm.addEventListener("submit", function(e){
    e.preventDefault();
    clearLookupError();
    var typed = (addrInput && addrInput.value || "").trim();
    if (!typed){ showLookupError("Enter your home address to pull the record."); return; }
    var address = (selectedPlace && selectedPlace.formatted_address) ? selectedPlace.formatted_address : typed;
    var lat = null, lng = null;
    if (selectedPlace && selectedPlace.geometry && selectedPlace.geometry.location){
      lat = selectedPlace.geometry.location.lat();
      lng = selectedPlace.geometry.location.lng();
    }
    track("net_sheet_lookup", { address: address });
    openGate(address, lat, lng);
  });

  if (gateForm) gateForm.addEventListener("submit", function(e){
    e.preventDefault();
    if (generating) return;
    clearGateError();
    var nameV = (gateName && gateName.value || "").trim();
    var emailV = (gateEmail && gateEmail.value || "").trim();
    var d = digits(gatePhone && gatePhone.value);
    if (!nameV){ showGateError("Please enter your name.", gateName); return; }
    if (!emailV || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailV)){ showGateError("Please enter a valid email so I can send the net sheet.", gateEmail); return; }
    if (d.length < 10){ showGateError("Please enter a 10-digit phone number.", gatePhone); return; }
    track("net_sheet_gate_submit", { address: pending.address });
    pullRecord(nameV, emailV, "(" + d.slice(0,3) + ") " + d.slice(3,6) + "-" + d.slice(6,10));
  });

  function pullRecord(name, email, phone){
    generating = true;
    if (gateSubmit){ gateSubmit.disabled = true; gateSubmit.textContent = "Pulling your record..."; }
    var gc = (window.funnelState && window.funnelState.gclid) || "";
    if (!gc){ try { gc = sessionStorage.getItem("drozq_gclid") || ""; } catch(e){} }
    var payload = {
      company_website: ($("ns-gate-hp") || {}).value || "",
      address: pending.address, lat: pending.lat, lng: pending.lng,
      name: name, full_name: name, email: email, phone: phone,
      consent: "yes", gclid: gc, source_page: "/net-sheet/", page_url: window.location.href
    };
    function reset(){
      generating = false;
      if (gateSubmit){ gateSubmit.disabled = false; gateSubmit.textContent = "Show my record"; }
    }
    fetch("/api/netsheet", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function(r){ return r.json().then(function(d){ return { ok: r.ok, status: r.status, data: d }; }); })
      .then(function(res){
        reset();
        if (!res.ok || !res.data || !res.data.ok){
          var code = (res.data && res.data.error) || "";
          /* A 200 ok:false (no record) and a 502 both saved the lead before
             returning, so "I've got your details" is true there. Config and
             validation failures save nothing: keep the dialog open to retry. */
          if (res.ok || code === "upstream_failed"){
            hideGate();
            showLookupError((res.data && res.data.message) ||
              "Thanks, I've got your details. I'll pull that record by hand and send the net sheet over. Or call me direct at (949) 438-5948.");
            var accEl = $("ns-acc");
            if (accEl) accEl.innerHTML = '<i>&#9888;</i><div><b>Still on generic defaults.</b> ' +
              "<span>I could not pull that record automatically, so fill in your annual tax bill and payoff " +
              "by hand, or let me send you the built version.</span></div>";
          } else {
            showGateError("Could not pull that record right now. Try again in a minute, or call me direct at (949) 438-5948.");
          }
          track("net_sheet_error", { error: code || "no_data", status: res.status });
          return;
        }
        hideGate();
        applyRecord(res.data);
        track("net_sheet_record_shown", {
          address: res.data.address ? res.data.address.formatted : pending.address,
          mello_roos: !!(res.data.taxes && res.data.taxes.specialAssessment && res.data.taxes.specialAssessment.detected)
        });
      })
      .catch(function(){
        reset();
        showGateError("Something went wrong pulling that record. Try again, or call (949) 438-5948.");
        track("net_sheet_error", { error: "network" });
      });
  }

  /* ---------------- render the record + prefill ------------------------- */
  function kv(label, value){ return '<div class="ns-kv"><span>' + esc(label) + "</span><b>" + value + "</b></div>"; }

  function applyRecord(d){
    RECORD = d;
    lastAddress = (d.address && d.address.formatted) || pending.address || "";
    if (d.costs && d.costs.cityTransfer) cityRule = d.costs.cityTransfer;

    var cards = [];
    var p = d.property || {}, a = d.address || {}, o = d.ownership, t = d.taxes || {}, est = d.estimate;

    /* the home */
    var homeRows = "";
    if (p.propertyType) homeRows += kv("Type", esc(p.propertyType));
    if (p.bedrooms || p.bathrooms) homeRows += kv("Beds / baths", (p.bedrooms || "?") + " / " + (p.bathrooms || "?"));
    if (p.squareFootage) homeRows += kv("Living area", p.squareFootage.toLocaleString() + " sqft");
    if (p.lotSize) homeRows += kv("Lot", p.lotSize.toLocaleString() + " sqft");
    if (p.yearBuilt) homeRows += kv("Built", String(p.yearBuilt));
    if (p.hoaMonthly) homeRows += kv("HOA dues", money(p.hoaMonthly) + "/mo");
    if (p.assessorID) homeRows += kv("Parcel", esc(p.assessorID));
    cards.push('<div class="ns-card"><h3>' + esc(a.formatted || lastAddress) + "</h3>" +
      (homeRows || '<span class="ns-hint">Limited attributes on the county record for this parcel.</span>') + "</div>");

    /* ownership */
    if (o){
      var oRows = "";
      if (o.ownerNames && o.ownerNames.length) oRows += kv("Owner of record", esc(o.ownerNames.join(", ")));
      if (o.lastSaleDate) oRows += kv("Last recorded sale", fmtDate(o.lastSaleDate));
      if (o.lastSalePrice) oRows += kv("Purchase price", money(o.lastSalePrice));
      if (o.yearsHeld != null) oRows += kv("Held", o.yearsHeld + (o.yearsHeld === 1 ? " year" : " years"));
      if (est) oRows += kv("Estimated value today", money(est.value));
      if (o.gainSincePurchase != null) oRows += kv("Change since purchase", signed(o.gainSincePurchase) + (o.gainPct != null ? " (" + o.gainPct + "%)" : ""));
      if (o.annualizedPct != null) oRows += kv("Annualized", o.annualizedPct + "% a year");
      if (o.ownerOccupied === false) oRows += kv("Occupancy", "Not owner-occupied on the roll");
      if (oRows) cards.push('<div class="ns-card"><h3>Ownership</h3>' + oRows +
        '<span class="ns-hint">County recorder deed records. Your purchase price is also your capital gains basis, before improvements.</span></div>');
    }

    /* tax bills */
    if (t.bills && t.bills.length){
      var rows = "";
      for (var i = 0; i < t.bills.length; i++){
        var b = t.bills[i], delta = "";
        if (i + 1 < t.bills.length && t.bills[i+1].total > 0){
          var dd = b.total - t.bills[i+1].total;
          var pct = (dd / t.bills[i+1].total * 100).toFixed(1);
          delta = dd >= 0 ? '<span class="ns-up">+' + pct + "%</span>" : '<span class="ns-dn">' + pct + "%</span>";
        }
        rows += "<tr><td>" + b.year + "</td><td><b>" + money(b.total) + "</b></td><td>" + delta + "</td></tr>";
      }
      cards.push('<div class="ns-card"><h3>Property tax billed</h3>' +
        '<table class="ns-bills"><thead><tr><th>Year</th><th>Total</th><th>Change</th></tr></thead><tbody>' +
        rows + "</tbody></table></div>");
    }

    /* assessed value + rate */
    if (t.assessed){
      var aRows = kv("Assessed value (" + t.assessed.year + ")", money(t.assessed.value));
      if (t.assessed.land) aRows += kv("Land", money(t.assessed.land));
      if (t.assessed.improvements) aRows += kv("Improvements", money(t.assessed.improvements));
      if (t.effectiveRate) aRows += kv("Your effective rate", (t.effectiveRate * 100).toFixed(3) + "%");
      if (t.countyAdValoremRate) aRows += kv("Typical ad valorem rate", (t.countyAdValoremRate * 100).toFixed(2) + "%");
      if (t.adValoremEstimate) aRows += kv("Ad valorem portion", money(t.adValoremEstimate));
      cards.push('<div class="ns-card"><h3>Assessed value and rate</h3>' + aRows +
        '<span class="ns-hint">Prop 13 caps the assessed increase at 2% a year, which is why a long-held home is assessed far under market.</span></div>');
    }

    /* Mello-Roos verdict */
    var sa = t.specialAssessment;
    if (sa){
      cards.push('<div class="ns-flag ' + (sa.detected ? "" : "ns-flag--clear") + '">' +
        '<span class="ns-pill-tag' + (sa.detected ? "" : " ns-pill-tag--ok") + '">' +
        (sa.detected ? "Special assessment detected" : "No special assessment") + "</span>" +
        '<p class="ns-flag-t">' + (sa.detected
          ? "Roughly " + money(sa.annual) + " a year of Mello-Roos or special assessment rides on this bill"
          : "This bill is ad valorem only") + "</p><p>" + esc(sa.note) +
        (sa.detected ? " Confirm the district and its bond payoff year on the tax bill under Special Assessment Charges before we price." : "") +
        "</p></div>");
    }

    /* the buyer's new bill */
    if (t.buyerNewBill){
      var nb = t.buyerNewBill;
      cards.push('<div class="ns-card"><h3>What the buyer will pay</h3>' +
        kv("Reassessed at", money(nb.assessedAt)) +
        kv("Ad valorem", money(nb.adValorem) + "/yr") +
        (nb.special ? kv("Special assessment", money(nb.special) + "/yr") : "") +
        kv("Their first full-year bill", money(nb.total)) +
        '<span class="ns-hint">' + esc(nb.note) + " Have the answer before it gets asked at an open house.</span></div>");
    }

    var grid = $("ns-rec-grid");
    if (grid) grid.innerHTML = cards.join("");
    var rec = $("ns-record");
    if (rec) rec.classList.add("is-on");

    /* Flip the accuracy strip: the numbers below are no longer generic. */
    var acc = $("ns-acc");
    if (acc){
      acc.classList.add("is-ok");
      acc.innerHTML = '<i>&#10003;</i><div><b>Built on the county record.</b> <span>' +
        esc(lastAddress) + ". Your tax bill, " +
        (t.specialAssessment && t.specialAssessment.detected ? "special assessment, " : "") +
        (p.hoaMonthly ? "HOA dues, " : "") +
        "and purchase are filled in below. Set your sale price and payoff and the rest is exact.</span></div>";
    }

    /* ---- prefill the calculator ---- */
    if (est && est.value) setVal("ns-price", est.value);
    if (t.latestBill && t.latestBill.total) setVal("ns-tax-annual", t.latestBill.total);
    if (p.hoaMonthly){ setVal("ns-hoa-monthly", p.hoaMonthly); setVal("ns-hoa-fees", 400); }
    if (o && o.lastSalePrice){
      setVal("ns-cg-basis", o.lastSalePrice);
      /* 20% down is the planning default; one field corrects it. */
      setVal("ns-p-orig", Math.round(o.lastSalePrice * 0.8));
      setVal("ns-t-orig", Math.round(o.lastSalePrice * 0.8));
    }
    if (o && o.lastSaleDate){
      var sd = pDate(o.lastSaleDate);
      if (sd){
        sd.setMonth(sd.getMonth() + 1); sd.setDate(1);
        var st = $("ns-p-start"); if (st) st.value = iso(sd);
        var st2 = $("ns-t-start"); if (st2) st2.value = iso(sd);
      }
    }
    var P0 = num($("ns-price"));
    setVal("ns-escrow", P0 > 0 ? 1200 + P0 * 0.001 : 0);
    setVal("ns-title",  P0 > 0 ? 500 + P0 * 0.0025 : 0);
    setVal("ns-tt-county", P0 * 0.0011);
    setVal("ns-tt-city", cityTransferTax(P0));

    /* Rewrite the city transfer tax hint so the seller sees WHY the number is
       what it is (or why it is zero). */
    var cityInput = $("ns-tt-city");
    var cityField = cityInput && cityInput.parentNode ? cityInput.parentNode.parentNode : null;
    var hintEl = cityField ? cityField.querySelector(".ns-hint") : null;
    if (hintEl){
      if (!cityRule || cityRule.kind === "none"){
        hintEl.textContent = (cityRule && cityRule.note) || "No city transfer tax here.";
      } else {
        var bits = [cityRule.label];
        if (cityRule.baseNote) bits.push(cityRule.baseNote);
        if (cityRule.tiers && cityRule.tiers.length){
          for (var ti = 0; ti < cityRule.tiers.length; ti++){
            if (P0 >= cityRule.tiers[ti].min && cityRule.tiers[ti].note){ bits.push(cityRule.tiers[ti].note); break; }
          }
        }
        if (cityRule.tierNote) bits.push(cityRule.tierNote);
        hintEl.textContent = bits.filter(Boolean).join(". ") + ".";
      }
    }

    /* Two of the three payment-mode fields are now filled from the deed, so
       land there: the seller only has to type the payment they already know. */
    if (o && o.lastSalePrice && !(num($("ns-payoff")) > 0)) setMode("payment");

    recalc();
    if (rec) setTimeout(function(){ try { rec.scrollIntoView({ behavior: "smooth", block: "start" }); } catch(e){} }, 60);
  }

  /* Deep link: /net-sheet/?address=... prefills and opens the gate. */
  try {
    var u = new URL(window.location.href);
    var pre = u.searchParams.get("address");
    if (pre && addrInput){
      addrInput.value = pre;
      setTimeout(function(){ if (lookupForm) lookupForm.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true })); }, 400);
    }
  } catch(e){}

  recalc();
})();
</script>"""
