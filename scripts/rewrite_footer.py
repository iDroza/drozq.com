"""
One-shot script: replace the homepage <footer id="footer">...</footer> block
with a minimal conversion-page footer.

Reads index.html, finds the unique <footer id="footer" ...> ... </footer> span
that is the LAST </footer> in the file, and rewrites it. Refuses to write if it
cannot find exactly one match.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

src = INDEX.read_text(encoding="utf-8")

start_marker = '<footer id="footer"'
end_marker = "</footer>"

start = src.find(start_marker)
if start < 0:
    sys.exit("Could not find <footer id=\"footer\">")

end = src.rfind(end_marker)
if end < 0 or end < start:
    sys.exit("Could not find closing </footer>")

end += len(end_marker)
old_footer = src[start:end]

# Sanity: make sure there is only one <footer id="footer"> in the file
if src.count(start_marker) != 1:
    sys.exit(f"Expected exactly one <footer id=\"footer\">, found {src.count(start_marker)}")

new_footer = (
    '<footer id="footer" class="pt_48px md:pt_64px pb_48px md:pb_64px c_white bg_footerBg ls_0.5px fs_10px lh_normal '
    '[&amp;_a]:c_white [&amp;_a]:td_none [&amp;_a]:bg-c_transparent [&amp;_a:hover]:td_underline '
    '[&amp;_a:focus]:ring_5px_auto_-webkit-focus-ring-color [&amp;_a:focus]:ring-o_-2px '
    '[&amp;_a:active,_&amp;_a:focus,_&amp;_a:visited]:c_white">'
    '<div class="pos_relative max-w_8xl mx_auto px_16px md:px_24px lg:max-w_1069px">'
    '<div class="d_flex flex-d_column ai_center jc_center ta_center gap_24px">'
    # Brand logo
    '<img height="25" width="165" src="/media/images/brand-logo-white.png" '
    'alt="Drozq logo, Joshua Guerrero Irvine real estate" loading="lazy" decoding="async">'
    # Identity / contact block
    '<div class="d_flex flex-d_column gap_8px fs_14px lh_2">'
    '<div>Drozq.com &middot; Real Brokerage</div>'
    '<div>California DRE #02267255</div>'
    '<div><a href="tel:9494385948" class="fw_bold">(949) 438-5948</a></div>'
    '</div>'
    # Social icons (Facebook, Instagram, YouTube)
    '<div class="d_flex gap_24px ai_center jc_center mt_8px">'
    '<a aria-label="link to Facebook social media" href="https://www.facebook.com/Drozq/" target="_blank" rel="nofollow noreferrer">'
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">'
    '<path fill="#FFF" fill-rule="evenodd" d="M10 20C4.477 20 0 15.523 0 10S4.477 0 10 0s10 4.477 10 10-4.477 10-10 10zm3.532-16.942L11.7 3.056c-2.059 0-3.39 1.341-3.39 3.418V8.05H6.47a.286.286 0 0 0-.288.283v2.283c0 .157.129.284.288.284H8.31v5.761c0 .157.129.283.288.283h2.404c.159 0 .288-.126.288-.283V10.9h2.154c.159 0 .288-.127.288-.284V8.333a.281.281 0 0 0-.084-.2.29.29 0 0 0-.204-.083h-2.154V6.714c0-.642.155-.968 1.006-.968h1.234a.286.286 0 0 0 .288-.284v-2.12a.286.286 0 0 0-.287-.284z" opacity=".87"></path>'
    '</svg></a>'
    '<a aria-label="link to Instagram social media" href="https://www.instagram.com/drozq/" target="_blank" rel="nofollow noreferrer">'
    '<svg height="20" viewBox="0 0 20 20" width="20" xmlns="http://www.w3.org/2000/svg">'
    '<path d="m10 20c-5.523 0-10-4.477-10-10s4.477-10 10-10 10 4.477 10 10-4.477 10-10 10zm0-15.693c1.854 0 2.074.007 2.806.04.79.036 1.524.195 2.088.759s.723 1.297.759 2.088c.033.732.04.952.04 2.806s-.007 2.074-.04 2.806c-.036.79-.195 1.524-.759 2.088s-1.297.723-2.088.759c-.732.033-.952.04-2.806.04s-2.074-.007-2.806-.04c-.79-.036-1.524-.195-2.088-.759s-.723-1.297-.759-2.088c-.033-.732-.04-.952-.04-2.806s.007-2.074.04-2.806c.036-.79.195-1.524.759-2.088s1.297-.723 2.088-.759c.732-.033.952-.04 2.806-.04zm0-1.251c-1.886 0-2.123.008-2.863.041-1.129.052-2.12.328-2.916 1.124s-1.072 1.787-1.124 2.916c-.033.74-.041.977-.041 2.863s.008 2.123.041 2.863c.052 1.129.328 2.12 1.124 2.916s1.787 1.072 2.916 1.124c.74.033.977.041 2.863.041s2.123-.008 2.863-.041c1.129-.052 2.12-.328 2.916-1.124s1.072-1.787 1.124-2.916c.033-.74.041-.977.041-2.863s-.008-2.123-.041-2.863c-.052-1.129-.328-2.12-1.124-2.916s-1.787-1.072-2.916-1.124c-.74-.033-.977-.041-2.863-.041zm0 3.378a3.566 3.566 0 1 0 0 7.132 3.566 3.566 0 0 0 0-7.132zm0 5.88a2.315 2.315 0 1 1 0-4.629 2.315 2.315 0 0 1 0 4.63zm3.707-5.188a.833.833 0 1 0 0-1.667.833.833 0 0 0 0 1.667z" fill="#fff" fill-rule="evenodd" opacity=".87"></path>'
    '</svg></a>'
    '<a aria-label="link to YouTube social media" href="https://www.youtube.com/@drozq" target="_blank" rel="nofollow noreferrer">'
    '<svg clip-rule="evenodd" fill-rule="evenodd" stroke-linejoin="round" stroke-miterlimit="2" viewBox="0 0 512 512" height="20" width="20" xmlns="http://www.w3.org/2000/svg" style="filter:invert(1);opacity:0.87">'
    '<path d="m256 0c141.29 0 256 114.71 256 256s-114.71 256-256 256-256-114.71-256-256 114.71-256 256-256zm153.315 178.978c-3.68-13.769-14.522-24.61-28.29-28.29-24.958-6.688-125.025-6.688-125.025-6.688s-100.067 0-125.025 6.688c-13.765 3.68-24.61 14.521-28.29 28.29-6.685 24.955-6.685 77.024-6.685 77.024s0 52.067 6.685 77.02c3.68 13.769 14.525 24.614 28.29 28.293 24.958 6.685 125.025 6.685 125.025 6.685s100.067 0 125.025-6.685c13.768-3.679 24.61-14.524 28.29-28.293 6.685-24.953 6.685-77.02 6.685-77.02s0-52.069-6.685-77.024zm-185.316 125.025v-96.002l83.137 48.001z"></path>'
    '</svg></a>'
    '</div>'
    # Legal links
    '<div class="d_flex flex-wrap_wrap gap_16px ai_center jc_center fs_14px lh_2 fw_normal">'
    '<a href="/privacy/">Privacy Policy</a>'
    '<span aria-hidden="true" class="op_0.5">&middot;</span>'
    '<a href="/terms/">Terms of Service</a>'
    '</div>'
    # Copyright
    '<div class="fs_12px lh_2 op_0.7 mt_8px">&copy; 2026 Drozq. All rights reserved.</div>'
    '</div></div></footer>'
)

new_src = src.replace(old_footer, new_footer, 1)

if new_src == src:
    sys.exit("Replacement produced no change")

INDEX.write_text(new_src, encoding="utf-8")
print(f"Old footer length: {len(old_footer)} chars")
print(f"New footer length: {len(new_footer)} chars")
print(f"File size change: {len(new_src) - len(src):+d} chars")
print("Footer rewritten.")
