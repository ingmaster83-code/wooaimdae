# 우아임대 (wooaimdae.wooahouse.com)
한국토지주택공사 전국 LH아파트 단지 정보(공공데이터포털 15080989) 중 주소·세대수가 있는 3,638단지(전세임대 제외) 기반 정적 사이트(약 4,000페이지).
- `data/lh.json`(커밋) → `python scripts/build_site.py` → `_site/`, 검증 `python scripts/check_site.py`
- 원본 CSV는 루트 `_pubdata_dl.py 15080989`로 받아 시도/시군구를 주소에서 파싱(세션에서 인라인 생성)
