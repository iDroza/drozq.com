// Test-only D1 stand-in over node:sqlite (Node 22.5+). Exposes the subset of
// the D1 API the functions use: prepare(sql).bind(...).run() / .first() /
// .all(), plus batch(). Real SQLite underneath, so UPSERT / RETURNING /
// datetime() behave exactly as they do on Cloudflare.
//
// Also exports fakeCache(): an in-memory caches.default with match()/put()
// honoring Cache-Control max-age, for exercising the Cache API fallbacks.
import { DatabaseSync } from "node:sqlite";

export function memoryD1(opts) {
  const db = new DatabaseSync(":memory:");
  const failOn = (opts && opts.failOn) || null;   // RegExp: throw on matching SQL
  const api = {
    _db: db,
    prepare(sql) {
      const make = (args) => ({
        async run() {
          if (failOn && failOn.test(sql)) throw new Error("simulated D1 failure");
          const r = db.prepare(sql).run(...args);
          return { success: true, meta: { changes: Number(r.changes || 0) } };
        },
        async first() {
          if (failOn && failOn.test(sql)) throw new Error("simulated D1 failure");
          const row = db.prepare(sql).get(...args);
          return row === undefined ? null : Object.assign({}, row);
        },
        async all() {
          if (failOn && failOn.test(sql)) throw new Error("simulated D1 failure");
          const rows = db.prepare(sql).all(...args).map((r) => Object.assign({}, r));
          return { success: true, results: rows, meta: {} };
        },
        bind(...more) { return make(more); }
      });
      return make([]);
    },
    async batch(stmts) {
      const out = [];
      for (const s of stmts) out.push(await s.run());
      return out;
    }
  };
  return api;
}

export function fakeCache() {
  const store = new Map();
  const keyOf = (req) => (typeof req === "string" ? req : req.url);
  return {
    _store: store,
    async match(req) {
      const k = keyOf(req);
      const hit = store.get(k);
      if (!hit) return undefined;
      if (hit.expires <= Date.now()) { store.delete(k); return undefined; }
      return new Response(hit.body, { status: 200, headers: { "content-type": "application/json" } });
    },
    async put(req, res) {
      const cc = res.headers.get("cache-control") || "";
      const m = /max-age=(\d+)/.exec(cc);
      const ttl = m ? Number(m[1]) : 60;
      store.set(keyOf(req), { body: await res.text(), expires: Date.now() + ttl * 1000 });
    }
  };
}

// Minimal Pages Function context.
export function makeContext(request, env) {
  const waits = [];
  return { request, env, waitUntil: (p) => waits.push(p), _waits: waits };
}

export function checker() {
  let pass = 0, fail = 0;
  return {
    check(label, cond, extra) {
      if (cond) { pass++; console.log("  ok   " + label); }
      else { fail++; console.log("  FAIL " + label + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
    },
    done() {
      console.log(`\n${pass} passed, ${fail} failed\n`);
      process.exit(fail ? 1 : 0);
    }
  };
}
