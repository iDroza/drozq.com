// Log redaction helpers. Cloudflare's real-time function logs are a shared
// surface (dashboard viewers, log exports), so lead PII never lands there in
// the clear except on the one deliberate recovery line (LEAD_NOT_DELIVERED,
// when no delivery channel is configured at all). Everything else logs the
// shape of the lead, not the lead: a masked email, the last four of the phone,
// the city-level part of an address, and never the name.

// "seller@example.com" -> "s***@example.com"
export function maskEmail(email) {
  const e = String(email == null ? "" : email).trim();
  if (!e) return "-";
  const at = e.lastIndexOf("@");
  if (at <= 0) return e.charAt(0) + "***";
  return e.charAt(0) + "***@" + e.slice(at + 1);
}

// "+1 (949) 555-0134" -> "***0134"
export function maskPhone(phone) {
  const digits = String(phone == null ? "" : phone).replace(/\D/g, "");
  if (!digits) return "-";
  return "***" + digits.slice(-4);
}

// "1 Example Way, Irvine, CA 92620" -> "Irvine, CA 92620"
// (drops the street line; keeps the locality so a log stays diagnosable)
export function maskAddress(address) {
  const a = String(address == null ? "" : address).trim();
  if (!a) return "-";
  const comma = a.indexOf(",");
  if (comma < 0) return "[address]";
  return a.slice(comma + 1).trim() || "[address]";
}

// "203.0.113.42" -> "203.0.*.*"    "2001:db8:85a3::8a2e:370:7334" -> "2001:db8:*"
export function maskIp(ip) {
  const s = String(ip == null ? "" : ip).trim();
  if (!s) return "-";
  if (s.indexOf(":") >= 0) {
    const groups = s.split(":");
    return groups.slice(0, 2).join(":") + ":*";
  }
  const parts = s.split(".");
  if (parts.length === 4) return parts[0] + "." + parts[1] + ".*.*";
  return "[ip]";
}
