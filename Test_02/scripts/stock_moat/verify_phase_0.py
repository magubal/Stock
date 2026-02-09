
import sys
import os

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from ksic_to_gics_mapper import KSICtoGICSMapper

def verify_namkwang():
    mapper = KSICtoGICSMapper()
    
    # 1. Test Namkwang Engineering (Construction) - KSIC 41101 (주거용 건물 건설업)
    # This was previously misclassified as IT Services due to fallback '4' or missing mapping.
    ksic_code = '41101'
    name = '남광토건'
    
    print(f"\n[Verification] Testing {name} (KSIC: {ksic_code})")
    result = mapper.map_to_gics(ksic_code, name)
    
    print(f"GICS Sector: {result['gics_sector']}")
    print(f"Korean Top: {result['korean_sector_top']}")
    print(f"Korean Sub: {result['korean_sector_sub']}")
    print(f"Reasoning: {result['reasoning']}")
    
    if result['gics_sector'] == 'Industrials' and result['korean_sector_top'] == '건설':
        print("\n✅ SUCCESS: Correctly classified as Construction (Industrials)")
    else:
        print("\n❌ FAILURE: Misclassified as " + result['gics_sector'])

    # 2. Test IT Services Strength
    # Should find typical_strength = 2 for IT Services
    gics_result = mapper.map_to_gics('620', '삼성SDS') # IT services
    moat_info = mapper.get_moat_drivers_by_gics(gics_result['gics_sector'], gics_result['gics_industry'])
    
    print(f"\n[Verification] Testing IT Services typical_strength")
    print(f"Industry: {gics_result['gics_industry']}")
    print(f"Typical Strength: {moat_info['typical_strength']}")
    
    if moat_info['typical_strength'] == 2:
        print("✅ SUCCESS: IT Services typical strength is correctly set to 2")
    else:
        print("❌ FAILURE: IT Services typical strength is " + str(moat_info['typical_strength']))

if __name__ == "__main__":
    verify_namkwang()
