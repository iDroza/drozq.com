// Sequence definitions: the actual drip copy, versioned in the repo so editing
// an email is a normal git commit. Two sequences exist:
//
//   lead-response-v1      every lead (funnel, One Tap, valuation, backfill).
//                         Four emails engineered to get a REPLY, not a click.
//   newsletter-welcome-v1 field-notes subscribers. One welcome email only:
//                         the /field-notes/ page promises "no marketing
//                         sequences, just the post," and the copy keeps that
//                         promise. Note drops go out as broadcasts.
//
// Copy rules (CLAUDE.md): first person, confident, specific. No em dashes.
// No anti-promise phrases. No vendor names. {first} and {city} are replaced
// per subscriber, with "there" / "Orange County" fallbacks.

function intentKind(intent) {
  const s = String(intent || "").toLowerCase();
  if (/purchase|buy/.test(s)) return "buy";
  if (/valuation|sell|sale/.test(s)) return "sell";
  return "neutral";
}

// The funnel's Places-confirmed street address ("214 Cedarwood Ln"). Naming
// the actual property is the strongest personalization signal we have; every
// use falls back gracefully when it is absent (buy leads, newsletter, backfill).
function cleanStreet(street) {
  const s = String(street || "").trim().replace(/,+$/, "").slice(0, 80);
  return s.length >= 4 ? s : "";
}

// One line keyed off the funnel's timeline answer, so the email proves it
// heard them. Exact option strings: "Yes, immediately" / "Yes, in 1-3 months"
// / "Yes, 4 or more months out" / "No, just curious". Unknown values get no
// line rather than a wrong one.
function timelineRead(timeline) {
  const s = String(timeline || "").toLowerCase();
  if (s.includes("immediately")) {
    return "You're moving now, so I'll lead with what it can close for in the next 30 days.";
  }
  if (s.includes("1-3")) {
    return "A 1 to 3 month window is real leverage: enough time to price at the top of the range instead of racing a deadline.";
  }
  if (s.includes("4 or more")) {
    return "With four or more months of runway, we time the market instead of taking it as it comes. I'll flag the window worth hitting.";
  }
  if (s.includes("curious")) {
    return "Curious is exactly the right time to get a real number: you move when the number says move, not when a deadline does.";
  }
  return "";
}

export const SEQUENCES = {
  "lead-response-v1": {
    steps: [
      {
        id: "instant-confirm",
        offsetDays: 0,
        subject(sub) {
          const k = intentKind(sub.intent);
          const street = cleanStreet(sub.street);
          if (street && k !== "buy") return street + ": I'm on it";
          if (k === "sell") return "Your home report request is in";
          if (k === "buy") return "Your {city} buyer plan is in";
          return "Got your request";
        },
        render(sub) {
          const k = intentKind(sub.intent);
          const street = cleanStreet(sub.street);
          const opener = street
            ? "Your request for **" + street + "** just came through drozq.com. I'm Joshua Guerrero, and I work every request personally."
            : "Your request just came through drozq.com. I'm Joshua Guerrero, and I work every request personally.";
          const nextStep = k === "buy"
            ? "Here's what happens next: I map your target against what homes like it are actually closing for in {city} right now. You get the real price to expect, where sellers are bending, and the move that wins the house without overpaying."
            : street
              ? "Here's what happens next: I pull the numbers on " + street + " and check them against what is actually closing around it right now. You get your real number, what would push it higher, and a straight answer on whether now is the time to sell."
              : "Here's what happens next: I pull your property's numbers and check them against what is actually closing near you right now. You get your real number, what would push it higher, and a straight answer on whether now is the time to sell.";
          const timelineLine = k === "buy" ? "" : timelineRead(sub.timeline);
          const question = k === "buy"
            ? "One question so I get this right: **what monthly payment would feel comfortable?** That one number tells me more than any wishlist."
            : k === "sell"
              ? "One question so I get this right: **what would the number have to be for you to seriously consider selling?**"
              : "One question so I get this right: **are you thinking about buying, selling, or both?**";
          return {
            preheader: street
              ? street + " hit my desk. One quick question and I get to work."
              : "Your request hit my desk. One quick question and I get to work.",
            headline: "I'm on it, {first}.",
            paragraphs: [
              opener,
              nextStep,
              timelineLine,
              question,
              "Hit reply. I read every response."
            ].filter(Boolean)
          };
        }
      },
      {
        id: "two-numbers",
        offsetDays: 2,
        subject() { return "The two numbers that matter in {city} right now"; },
        render() {
          return {
            preheader: "Live rates and live prices, updated daily. Two minutes beats an hour of news.",
            headline: "Price your move on live data, not headlines.",
            paragraphs: [
              "Most people plan a move on headlines, and headlines run weeks behind the market. I keep two live readouts on my site instead: today's locked mortgage rates by loan program, and what Southern California home prices are actually doing.",
              "Both update daily. Two minutes there beats an hour of news, and it's the same data I use when I advise a client to move or to wait.",
              "Where does your timeline sit: making a move this year, or watching for the right window? Reply with either one and I'll tailor what I send you."
            ],
            ctaLabel: "See today's numbers",
            ctaUrl: "https://drozq.com/rates/"
          };
        }
      },
      {
        id: "case-file",
        offsetDays: 5,
        subject() { return "How $23,250 in seller credit actually happened"; },
        render() {
          return {
            preheader: "A real transaction, documented with the real numbers.",
            headline: "The receipts, not the pitch.",
            paragraphs: [
              "A Long Beach firefighter came to me as a first-time buyer. By closing, we had negotiated $23,250 in seller credit. The full case file is on my site: the numbers, the sequence, and what almost went sideways.",
              "Every client file gets documented like that, because the numbers are the argument.",
              "Want me to run your numbers the same way? Reply with the words **run it** and I'll start today."
            ],
            ctaLabel: "Read the case file",
            ctaUrl: "https://drozq.com/testimonials/001-long-beach-firefighter/"
          };
        }
      },
      {
        id: "nine-word",
        offsetDays: 10,
        subject() { return "{first}, quick question"; },
        render(sub) {
          const k = intentKind(sub.intent);
          const street = cleanStreet(sub.street);
          const q = k === "buy"
            ? "Are you still looking at homes in {city}?"
            : street
              ? "Are you still thinking about selling " + street + "?"
              : k === "sell"
                ? "Are you still thinking about selling your home in {city}?"
                : "Are you still planning a move in {city}?";
          return {
            preheader: "One-word replies are fine.",
            headline: "",
            paragraphs: [
              q,
              "A one-word reply is plenty. I'll take it from there."
            ]
          };
        }
      }
    ]
  },

  "newsletter-welcome-v1": {
    steps: [
      {
        id: "welcome",
        offsetDays: 0,
        subject() { return "You're on the list"; },
        render() {
          return {
            preheader: "One email when a new note goes live. That's the deal.",
            headline: "Welcome to Field Notes.",
            paragraphs: [
              "You'll get one email the moment a new note goes live. That's the deal, and I keep it.",
              "While you're here: I keep live readouts of mortgage rates and Southern California home prices on the site, updated daily. Same data I work from.",
              "One question: are you buying, selling, or just watching the market? A one-word reply is perfect. It tells me which notes to write next."
            ],
            ctaLabel: "See the live numbers",
            ctaUrl: "https://drozq.com/rates/"
          };
        }
      }
    ]
  }
};

// Which sequence a new subscriber enters, from how they arrived.
export function sequenceIdFor(source, intent) {
  if (String(intent || "") === "Field Notes Subscribe") return "newsletter-welcome-v1";
  if (String(source || "") === "newsletter" || String(source || "") === "field-notes-subscribe") return "newsletter-welcome-v1";
  return "lead-response-v1";
}

export function getSequence(id) {
  return SEQUENCES[id] || null;
}
