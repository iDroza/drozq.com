// Tests for functions/_lib/csv.js (the subscriber-export formula guard).
// Run:  node scripts/test_csv_guard.mjs
import { csvCell, csvLine } from "../functions/_lib/csv.js";
import { checker } from "./_test_d1.mjs";

const { check, done } = checker();

console.log("\n== plain cells pass through ==");
check("plain text", csvCell("Pat Sample") === "Pat Sample");
check("null -> empty", csvCell(null) === "" && csvCell(undefined) === "");
check("number", csvCell(42) === "42");
check("email untouched (@ is not leading)", csvCell("pat@example.com") === "pat@example.com");

console.log("\n== RFC 4180 quoting ==");
check("comma quoted", csvCell("Irvine, CA") === '"Irvine, CA"');
check("double quote doubled", csvCell('say "hi"') === '"say ""hi"""');
check("newline quoted", csvCell("a\nb") === '"a\nb"');
check("carriage return inside quoted", csvCell("a\rb") === '"a\rb"');

console.log("\n== formula-injection guard ==");
check("= prefixed", csvCell("=HYPERLINK(\"http://evil\",\"x\")") === "\"'=HYPERLINK(\"\"http://evil\"\",\"\"x\"\")\"");
check("+ prefixed", csvCell("+1+2") === "'+1+2");
check("- prefixed", csvCell("-2+3+cmd|' /C calc'!A0") === "'-2+3+cmd|' /C calc'!A0");
check("@ prefixed", csvCell("@SUM(1,2)") === "\"'@SUM(1,2)\"");
check("tab prefixed", csvCell("\t=1+1") === "'\t=1+1");
check("CR prefixed (also quoted)", csvCell("\r=1+1") === "\"'\r=1+1\"");
check("negative-looking phone kept literal", csvCell("-949-555-0134") === "'-949-555-0134");
check("interior = untouched", csvCell("a=b") === "a=b");

console.log("\n== csvLine ==");
check("line joins guarded cells", csvLine(["id", "=cmd", "x,y"]) === 'id,\'=cmd,"x,y"');

done();
