"""Quick test for GICS mapping fix"""
import sys
sys.path.insert(0, 'F:/PSJ/AntigravityWorkPlace/Stock/Test_02/.agent/skills/stock-moat/utils')
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from ksic_to_gics_mapper import KSICtoGICSMapper

mapper = KSICtoGICSMapper()

tests = [
    ('58221', '엔씨소프트', '게임', '게임소프트웨어'),
    ('58222', '폴라리스오피스', 'IT', '응용SW'),
    ('58219', '데이타솔루션', 'IT', '응용SW'),
    ('582', '카카오', 'IT', '소프트웨어'),
    ('639', 'KTis', 'IT', '정보서비스'),
    ('620', 'MDS테크', 'IT', 'IT서비스'),
    ('58221', '딥노이드', 'IT', 'AI/딥러닝'),
    ('58221', '마음AI', 'IT', 'AI/음성합성'),
    ('58221', '알체라', 'IT', 'AI/영상인식'),
]

passed = 0
failed = 0
for ksic, name, exp_top, exp_sub in tests:
    r = mapper.map_to_gics(ksic, name)
    top = r['korean_sector_top']
    sub = r['korean_sector_sub']
    src = r['source']
    conf = r['confidence']
    ok = top == exp_top and sub == exp_sub
    mark = '✅' if ok else '❌'
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"{mark} {name:15} KSIC={ksic:6} => {top}/{sub:15} (src={src}, conf={conf:.2f})")
    if not ok:
        print(f"   Expected: {exp_top}/{exp_sub}")

print(f"\nResult: {passed} passed, {failed} failed out of {len(tests)}")
