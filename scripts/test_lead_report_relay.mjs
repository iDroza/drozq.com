import assert from "node:assert/strict";
import { onRequestPost } from "../functions/api/lead.js";


function makeRequest(origin) {
  const body = new FormData();
  body.set("name", "Relay Test");
  body.set("email", "relay-test@example.com");
  body.set("phone", "9495551212");
  body.set("consent", "yes");
  body.set("intent", "Home Valuation");
  body.set("full_address", "123 Test St, Irvine, CA 92614");
  body.set("street_address", "123 Test St");
  body.set("city", "Irvine");
  body.set("state", "CA");
  body.set("zip", "92614");
  body.set("source_page", "homepage funnel");
  body.set("delivery_scope", "report_only");
  body.set("source_host", "activerealty.com");
  return new Request("https://drozq.com/api/lead", {
    method: "POST",
    headers: { origin },
    body
  });
}


async function run(origin) {
  const calls = [];
  const pending = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
  };
  try {
    const response = await onRequestPost({
      request: makeRequest(origin),
      env: {
        TO_EMAIL: "owner@example.com",
        FROM_EMAIL: "site@example.com",
        MAILCHANNELS_API_KEY: "test-mailchannels",
        ZAPIER_WEBHOOK_URL: "https://hooks.example.com/lead",
        FOLLOWUPBOSS_API_KEY: "test-fub"
      },
      waitUntil(promise) { pending.push(promise); }
    });
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), { ok: true });
    await Promise.all(pending);
    return calls;
  } finally {
    globalThis.fetch = originalFetch;
  }
}


const activeCalls = await run("https://www.activerealty.com");
assert.equal(activeCalls.length, 0, "authorized Active relay must suppress duplicate lead channels");

const untrustedCalls = await run("https://example.com");
assert.equal(untrustedCalls.length, 3, "untrusted origins must retain normal lead delivery");
assert(untrustedCalls.some((call) => call.url.includes("mailchannels.net")));
assert(untrustedCalls.some((call) => call.url.includes("hooks.example.com")));
assert(untrustedCalls.some((call) => call.url.includes("followupboss.com")));

console.log("PASS lead report-only relay isolation");
