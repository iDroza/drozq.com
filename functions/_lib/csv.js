// CSV cell encoding with a formula-injection guard. Subscriber exports open in
// Excel / Sheets, which evaluate any cell starting with = + - @ (and treat a
// leading tab or carriage return as a lead-in to one). A subscriber whose
// "name" is `=HYPERLINK(...)` or `-2+3+cmd|...` must land as literal text, so
// such cells are prefixed with a single quote (the spreadsheet convention for
// "this is text") before the usual RFC 4180 quoting.

const FORMULA_LEAD = /^[=+\-@\t\r]/;

export function csvCell(v) {
  let s = v == null ? "" : String(v);
  if (FORMULA_LEAD.test(s)) s = "'" + s;
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

export function csvLine(values) {
  return values.map(csvCell).join(",");
}
