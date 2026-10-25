# -*- coding: utf-8 -*-
"""우아임대 정적 사이트 생성기 → _site/.  사용: python scripts/build_site.py  (data/lh.json 필요)"""
import sys, json, re, shutil, time, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import *

A = json.loads((ROOT / "data" / "lh.json").read_text(encoding="utf-8"))
ASOF = "LH 단지 현황 공공데이터"

def table(heads, rows, num=()):
    th = "".join('<th%s>%s</th>' % (' class="num"' if i in num else "", h) for i, h in enumerate(heads))
    body = "".join("<tr>%s</tr>" % "".join('<td%s>%s</td>' % (' class="num"' if i in num else "", v) for i, v in enumerate(r)) for r in rows)
    return '<div class="tbl-wrap"><table class="tbl"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, body)

def chips(items): return '<div class="chips">%s</div>' % "".join('<a class="chip" href="%s">%s</a>' % (u, esc(t)) for t, u in items)
def sl(s): return re.sub(r"[^0-9A-Za-z가-힣]+", "-", s).strip("-") or "x"
def dt(s): return s.replace("-", ".") if s else ""
NOTE = "LH 단지 정보는 한국토지주택공사 공공데이터를 정리한 참고용입니다. 입주 자격·모집 일정·임대조건은 공고문마다 다르니 신청 전 마이홈포털(myhome.go.kr)과 LH청약플러스의 공고문을 반드시 확인하세요. 청약·입주 권유가 아닙니다."
SIDO_ORDER = ["서울특별시", "부산광역시", "대구광역시", "인천광역시", "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원특별자치도", "충청북도", "충청남도", "전북특별자치도", "전남광주통합특별시", "광주광역시", "전라남도", "경상북도", "경상남도", "제주특별자치도"]
SIDO_SHORT = {s: s.replace("특별자치도", "").replace("특별자치시", "").replace("특별시", "").replace("광역시", "") for s in SIDO_ORDER}
TYPE_DESC = {"국민임대": "소득과 자산 요건을 갖춘 무주택 서민을 대상으로 하는 임대주택입니다.", "영구임대": "생계급여·의료급여 수급자 등 저소득 취약계층을 위한 장기 임대주택입니다.", "행복주택": "청년·신혼부부·고령자 등 주거 취약계층을 위한 임대주택입니다.",
             "공공임대(5년)": "5년 임대 후 분양 전환이 가능한 공공임대주택입니다.", "공공임대(10년)": "10년 임대 후 분양 전환이 가능한 공공임대주택입니다.", "공공분양": "공공이 공급하는 분양 주택입니다.", "분양주택": "분양으로 공급된 주택 단지입니다.",
             "통합공공임대": "영구·국민·행복주택 등을 통합한 공공임대주택입니다.", "신축다세대매입임대": "LH가 신축 다세대주택을 사들여 임대하는 매입임대주택입니다.", "기존주택매입임대": "LH가 기존 주택을 사들여 임대하는 매입임대주택입니다."}

for a in A:
    a["slug"] = sl(a["n"])[:40] + "-" + a["c"]; a["path"] = "/complex/%s/%s/" % (sl(SIDO_SHORT.get(a["sido"], a["sido"])), a["slug"])
    a["year"] = (a["done"][:4] or a["ms"][:4] or "미상")
    a["tmain"] = a["type"].split("+")[0]
A.sort(key=lambda a: (-a["hh"], a["n"]))
BY_SIDO = collections.defaultdict(list); BY_SG = collections.defaultdict(list); BY_TYPE = collections.defaultdict(list); BY_YEAR = collections.defaultdict(list); BY_HQ = collections.defaultdict(list)
for a in A:
    BY_SIDO[a["sido"]].append(a); BY_SG[(a["sido"], a["sg"])].append(a); BY_TYPE[a["tmain"]].append(a); BY_YEAR[a["year"]].append(a); BY_HQ[a["hq"]].append(a)
SIDOS = [s for s in SIDO_ORDER if s in BY_SIDO]
TSLUG = {t: sl(t) for t in BY_TYPE}
TYPES_OK = {t for t in BY_TYPE if len(BY_TYPE[t]) >= 5}
DUPN = collections.Counter((a["n"], a["sg"], a["tmain"], a["hh"]) for a in A)
def sp(s): return sl(SIDO_SHORT.get(s, s))
def rp(s, g=None): return "/region/%s/" % sp(s) + (("%s/" % sl(g)) if g else "")
def hh_s(n): return "{:,}세대".format(n)
def arow(a): return ['<a href="%s">%s</a>' % (a["path"], esc(a["n"])), esc(a["sido"].replace("특별자치도", "").replace("특별시", "").replace("광역시", "") + " " + a["sg"]), esc(a["tmain"]), hh_s(a["hh"]), esc(dt(a["done"]) or "-")]
AH = ["단지", "지역", "유형", "세대수", "준공일"]
def stats(lst): return "%d단지·%s세대" % (len(lst), "{:,}".format(sum(a["hh"] for a in lst)))

# ── 단지 ──
def page_c(a):
    sg = BY_SG[(a["sido"], a["sg"])]; rank_sg = [x["c"] for x in sg].index(a["c"]) + 1
    rank_n = [x["c"] for x in A].index(a["c"]) + 1
    same = [x for x in sg if x is not a][:6]; samet = [x for x in BY_TYPE[a["tmain"]] if x is not a and x["sido"] == a["sido"]][:5]
    avg_dong = round(a["hh"] / a["dg"]) if a["dg"] else None
    lead = (f"<p class=\"lead\"><b>{esc(a['n'])}</b>은(는) {esc(a['addr'])}에 있는 LH <b>{esc(a['lease'])}</b>({esc(a['type'])}) 단지로 총 <b>{hh_s(a['hh'])}</b>{(', ' + str(a['dg']) + '개 동') if a['dg'] else ''}입니다. "
            f"{('준공일은 ' + dt(a['done']) + ', ') if a['done'] else ''}{('입주 지정 기간은 ' + dt(a['ms']) + (' ~ ' + dt(a['me']) if a['me'] else '') + '입니다. ') if a['ms'] else ''}"
            f"{esc(a['sg'])} LH 단지 {len(sg)}곳 중 세대수 {rank_sg}위이고 전국 {len(A):,}곳 중 {rank_n:,}위입니다.</p>")
    rows = [["단지명", esc(a["n"])], ["단지코드", a["c"]], ["지역본부", esc(a["hq"])], ["유형", "%s · %s" % (esc(a["lease"]), esc(a["type"]))], ["주소", esc(a["addr"])], ["세대수", hh_s(a["hh"])]]
    if a["dg"]: rows.append(["동수", "%d개 동" % a["dg"]])
    if avg_dong: rows.append(["동당 평균 세대", "약 %d세대" % avg_dong])
    if a["done"]: rows.append(["준공일", dt(a["done"])])
    if a["ms"]: rows.append(["입주 지정 기간", dt(a["ms"]) + (" ~ " + dt(a["me"]) if a["me"] else "")])
    td = TYPE_DESC.get(a["tmain"])
    tb = ('<h2 class="group-title">🏷️ %s이란?</h2><p class="lead">%s 입주 자격은 공고문과 소득·자산 기준에 따라 다르니 마이홈포털에서 확인하세요.</p>' % (esc(a["tmain"]), td)) if td else ""
    ns = ('<h2 class="group-title">📍 같은 지역의 다른 LH 단지</h2>' + table(AH, [arow(x) for x in same])) if same else ""
    nt = ('<h2 class="group-title">🔁 같은 유형(%s) 다른 단지</h2>' % esc(a["tmain"]) + table(AH, [arow(x) for x in samet])) if samet else ""
    body = f"""
<div class="page-head"><h1>{esc(a['n'])} — LH {esc(a['tmain'])} {hh_s(a['hh'])}</h1><p>{esc(a['sido'])} {esc(a['sg'])} · {esc(a['lease'])}</p></div>
{lead}
{ad()}
<h2 class="group-title">📋 단지 정보</h2>
{table(['항목', '내용'], rows)}
{tb}
{ns}
{nt}
<p class="note">{NOTE}</p>
{chips([(a["sg"] + " LH 단지", rp(a["sido"], a["sg"])), (a["tmain"], "/type/%s/" % TSLUG[a["tmain"]]) if a["tmain"] in TYPES_OK else ("임대 유형", "/type/"), (a["year"] + "년", "/year/%s/" % a["year"]), ("임대 유형 안내", "/guide/")])}
"""
    faq = [(f"{a['n']}은(는) 몇 세대인가요?", f"{hh_s(a['hh'])}{(', ' + str(a['dg']) + '개 동') if a['dg'] else ''}입니다."), (f"{a['n']}은(는) 어떤 유형인가요?", f"{a['lease']}({a['type']}) 단지입니다."), ("입주 신청은 어디서 하나요?", "마이홈포털과 LH청약플러스의 모집공고를 확인해 신청합니다.")]
    write(a["path"], layout(a["path"], f"{a['n']}{(' (' + a['c'] + ')') if DUPN[(a['n'], a['sg'], a['tmain'], a['hh'])] > 1 else ''} — {a['sg']} LH {a['tmain']} {hh_s(a['hh'])}", f"{a['n']}({a['addr']}) LH {a['lease']} {a['type']} {hh_s(a['hh'])}. {('준공 ' + dt(a['done']) + '. ') if a['done'] else ''}지역·유형별 비교.", body, faq,
          [("홈", "/"), ("지역별", "/region/"), (a["sido"], rp(a["sido"])), (a["sg"], rp(a["sido"], a["sg"])), (a["n"], a["path"])]), "0.5")

# ── 지역 ──
def page_sg(s, g):
    lst = BY_SG[(s, g)]; path = rp(s, g); tc = collections.Counter(a["tmain"] for a in lst)
    body = f"""
<div class="page-head"><h1>{esc(g)} LH 임대·분양 단지 {len(lst)}곳 — 세대수·유형</h1><p>{esc(s)} {esc(g)} · {stats(lst)}</p></div>
<p class="lead"><b>{esc(s)} {esc(g)}</b>에는 LH 임대·분양 단지가 {len(lst)}곳({stats(lst)})입니다. 유형별로는 {', '.join('%s %d곳' % (k, v) for k, v in tc.most_common(5))} 순입니다. 세대수가 많은 순으로 보여 드립니다.</p>
{ad()}
{table(AH, [arow(a) for a in lst])}
<p class="note">{NOTE}</p>
{chips([(s, rp(s)), ("임대 유형 안내", "/guide/"), ("지역별", "/region/")])}
"""
    faq = [(f"{g}에는 LH 단지가 몇 곳 있나요?", f"공공데이터 기준 {len(lst)}곳({stats(lst)})입니다."), (f"{g}에서 가장 큰 LH 단지는?", f"{lst[0]['n']}({hh_s(lst[0]['hh'])})입니다.")]
    write(path, layout(path, f"{s} {g} LH 임대·분양 단지 {len(lst)}곳 — 세대수·유형", f"{s} {g} LH 단지 {len(lst)}곳({stats(lst)}). 가장 큰 단지 {lst[0]['n']}.", body, faq, [("홈", "/"), ("지역별", "/region/"), (s, rp(s)), (g, path)]), "0.7")

def page_sido(s):
    lst = BY_SIDO[s]; path = rp(s); sgs = collections.Counter(a["sg"] for a in lst); tc = collections.Counter(a["tmain"] for a in lst)
    body = f"""
<div class="page-head"><h1>{esc(s)} LH 임대·분양 단지 {len(lst)}곳</h1><p>{stats(lst)}</p></div>
<p class="lead"><b>{esc(s)}</b>의 LH 임대·분양 단지는 {len(lst)}곳({stats(lst)})입니다. 유형별로는 {', '.join('%s %d곳' % (k, v) for k, v in tc.most_common(5))} 순입니다. 시군구를 눌러 단지 목록을 확인하세요.</p>
{ad()}
{chips([("%s %d곳" % (g, c), rp(s, g)) for g, c in sgs.most_common()])}
<h2 class="group-title">🏆 세대수 많은 단지 TOP 20</h2>
{table(AH, [arow(a) for a in lst[:20]])}
<p class="note">{NOTE}</p>
{chips([("지역별", "/region/"), ("임대 유형 안내", "/guide/")])}
"""
    faq = [(f"{s}에는 LH 단지가 몇 곳 있나요?", f"공공데이터 기준 {len(lst)}곳입니다.")]
    write(path, layout(path, f"{s} LH 임대·분양 단지 {len(lst)}곳 — 시군구별 목록", f"{s} LH 단지 {len(lst)}곳({stats(lst)}). 시군구별 단지와 세대수.", body, faq, [("홈", "/"), ("지역별", "/region/"), (s, path)]), "0.8")
    for g in sgs: page_sg(s, g)

def hub_region():
    rows = [['<a href="%s">%s</a>' % (rp(s), esc(s)), len(BY_SIDO[s]), "{:,}".format(sum(a["hh"] for a in BY_SIDO[s]))] for s in SIDOS]
    body = f"""
<div class="page-head"><h1>지역별 LH 임대·분양 단지 — 전국 {len(A):,}곳</h1><p>{stats(A)}</p></div>
<p class="lead">전국 LH 임대·분양 단지 {len(A):,}곳({stats(A)})을 시도·시군구별로 정리했습니다. 지역을 선택하면 단지명·유형·세대수·준공일을 볼 수 있습니다.</p>
{ad()}
{table(['시도', '단지', '세대'], rows, (1, 2))}
<p class="note">{NOTE}</p>
{chips([("임대 유형", "/type/"), ("준공연도", "/year/"), ("대단지 순위", "/rank/")])}
"""
    write("/region/", layout("/region/", f"지역별 LH 임대·분양 단지 — 전국 {len(A):,}곳 세대수·유형", f"전국 LH 임대·분양 단지 {len(A):,}곳을 시도·시군구별로 정리했습니다.", body, [("전국에 LH 단지는 몇 곳인가요?", f"공공데이터 기준 {len(A):,}곳({stats(A)})입니다.")], [("홈", "/"), ("지역별", "/region/")], coupang=True), "0.9")

# ── 유형·연도·본부·순위 ──
def page_type(t):
    lst = BY_TYPE[t]; path = "/type/%s/" % TSLUG[t]; sc = collections.Counter(a["sido"] for a in lst)
    body = f"""
<div class="page-head"><h1>LH {esc(t)} 단지 {len(lst)}곳 — 지역·세대수</h1><p>{stats(lst)}</p></div>
<p class="lead"><b>{esc(t)}</b> 단지는 전국에 {len(lst)}곳({stats(lst)})입니다. {TYPE_DESC.get(t, '')} 지역별로는 {', '.join('%s %d곳' % (SIDO_SHORT.get(k, k), v) for k, v in sc.most_common(5))} 순입니다.</p>
{ad()}
{table(AH, [arow(a) for a in lst[:200]])}
{('<p class="note">세대수 상위 200곳만 표시했습니다. 지역별 목록에서 전체를 볼 수 있습니다.</p>') if len(lst) > 200 else ''}
<p class="note">{NOTE}</p>
{chips([("임대 유형 안내", "/guide/"), ("지역별", "/region/")])}
"""
    faq = [(f"{t}란?", TYPE_DESC.get(t, "LH가 공급한 주택 유형입니다.")), (f"{t} 단지는 몇 곳인가요?", f"공공데이터 기준 {len(lst)}곳입니다.")]
    write(path, layout(path, f"LH {t} 단지 {len(lst)}곳 — 전국 목록·세대수", f"LH {t} 단지 {len(lst)}곳({stats(lst)}) 전국 목록. 지역별 세대수와 준공일.", body, faq, [("홈", "/"), ("임대 유형", "/type/"), (t, path)]), "0.7")

def hub_type():
    ts = list(TYPES_OK)
    rows = [['<a href="/type/%s/">%s</a>' % (TSLUG[t], esc(t)), len(BY_TYPE[t]), "{:,}".format(sum(a["hh"] for a in BY_TYPE[t])), esc(TYPE_DESC.get(t, ""))] for t in sorted(ts, key=lambda t: -len(BY_TYPE[t]))]
    body = f"""
<div class="page-head"><h1>LH 임대 유형별 단지 — 국민임대·영구임대·행복주택·공공분양</h1><p>유형별 단지 수</p></div>
<p class="lead">LH 단지를 주택 유형별로 정리했습니다. 유형을 누르면 전국 단지 목록과 지역별 분포를 볼 수 있습니다.</p>
{ad()}
{table(['유형', '단지', '세대', '설명'], rows, (1, 2))}
<p class="note">{NOTE}</p>
"""
    write("/type/", layout("/type/", "LH 임대 유형별 단지 — 국민임대·영구임대·행복주택·공공분양", "LH 국민임대·영구임대·행복주택·공공임대·공공분양 단지를 유형별로 정리했습니다.", body, [("국민임대와 행복주택의 차이는?", "대상 계층이 다릅니다. 국민임대는 소득·자산 요건을 갖춘 무주택 서민, 행복주택은 청년·신혼부부·고령자 등 주거 취약계층이 대상입니다.")], [("홈", "/"), ("임대 유형", "/type/")], coupang=True), "0.8")
    for t in ts: page_type(t)

def page_year(y):
    lst = BY_YEAR[y]; path = "/year/%s/" % y; tc = collections.Counter(a["tmain"] for a in lst)
    body = f"""
<div class="page-head"><h1>{y}년 {'준공·입주' if y != '미상' else '준공 시기 미상'} LH 단지 {len(lst)}곳</h1><p>{stats(lst)}</p></div>
<p class="lead">{y}년에 준공(또는 입주 시작)한 LH 단지는 {len(lst)}곳({stats(lst)})입니다. 유형별로는 {', '.join('%s %d곳' % (k, v) for k, v in tc.most_common(4))} 순입니다.</p>
{ad()}
{table(AH, [arow(a) for a in lst[:200]])}
{('<p class="note">세대수 상위 200곳만 표시했습니다.</p>') if len(lst) > 200 else ''}
<p class="note">{NOTE}</p>
{chips([("준공연도", "/year/"), ("지역별", "/region/")])}
"""
    write(path, layout(path, f"{y}년 {'준공·입주' if y != '미상' else '준공 시기 미상'} LH 단지 {len(lst)}곳 — 지역·세대수", f"{y}년 준공·입주 LH 단지 {len(lst)}곳({stats(lst)}).", body, [(f"{y}년 LH 단지는 몇 곳인가요?", f"공공데이터 기준 {len(lst)}곳입니다.")], [("홈", "/"), ("준공연도", "/year/"), (y, path)]), "0.5")

def hub_year():
    ys = sorted(BY_YEAR, reverse=True)
    body = f"""
<div class="page-head"><h1>준공연도별 LH 단지 — 입주 시기로 찾기</h1><p>연도별 단지 수</p></div>
<p class="lead">LH 단지를 준공(또는 입주 시작) 연도별로 정리했습니다. 연도를 누르면 해당 연도 단지 목록을 볼 수 있습니다.</p>
{ad()}
{chips([("%s년 %d곳" % (y, len(BY_YEAR[y])) if y != "미상" else "시기 미상 %d곳" % len(BY_YEAR[y]), "/year/%s/" % y) for y in ys])}
<p class="note">{NOTE}</p>
"""
    write("/year/", layout("/year/", "준공연도별 LH 단지 — 입주 시기로 찾는 임대·분양 단지", "LH 단지를 준공·입주 연도별로 정리했습니다.", body, [("신축 LH 단지는 어떻게 찾나요?", "최근 연도를 선택하면 해당 연도 준공 단지가 나옵니다.")], [("홈", "/"), ("준공연도", "/year/")]), "0.7")
    for y in ys: page_year(y)

def page_rank(s=None):
    lst = (BY_SIDO[s] if s else A)[:100 if not s else 30]; path = "/rank/%s" % ((sp(s) + "/") if s else "")
    nm = esc(s) if s else "전국"
    body = f"""
<div class="page-head"><h1>{nm} LH 대단지 순위 TOP {len(lst)} — 세대수 많은 단지</h1><p>세대수 기준</p></div>
<p class="lead">{nm} LH 단지 중 세대수가 많은 순위입니다. 1위는 <b>{esc(lst[0]['n'])}</b>({esc(lst[0]['sg'])}, {hh_s(lst[0]['hh'])})입니다.</p>
{ad()}
{table(['순위'] + AH, [[i + 1] + arow(a) for i, a in enumerate(lst)], (0,))}
<p class="note">{NOTE}</p>
{chips([("전국 순위", "/rank/"), ("지역별", "/region/")])}
"""
    write(path, layout(path, f"{nm} LH 대단지 순위 TOP {len(lst)} — 세대수 많은 임대·분양 단지", f"{nm} LH 단지 세대수 순위. 1위 {lst[0]['n']}({hh_s(lst[0]['hh'])}).", body, [(f"{nm}에서 가장 큰 LH 단지는?", f"{lst[0]['n']}({hh_s(lst[0]['hh'])})입니다.")], [("홈", "/"), ("대단지 순위", "/rank/")] + ([(s, path)] if s else [])), "0.7" if not s else "0.5")

def page_hq(h):
    lst = BY_HQ[h]; path = "/hq/%s/" % sl(h)
    body = f"""
<div class="page-head"><h1>LH {esc(h)} 관할 단지 {len(lst)}곳</h1><p>{stats(lst)}</p></div>
<p class="lead"><b>{esc(h)}</b> 관할 LH 단지는 {len(lst)}곳({stats(lst)})입니다. 세대수 많은 순입니다.</p>
{ad()}
{table(AH, [arow(a) for a in lst[:200]])}
<p class="note">{NOTE}</p>
{chips([("지역별", "/region/"), ("임대 유형", "/type/")])}
"""
    write(path, layout(path, f"LH {h} 관할 단지 {len(lst)}곳 — 세대수·유형", f"LH {h} 관할 임대·분양 단지 {len(lst)}곳({stats(lst)}).", body, [(f"{h} 관할 단지는 몇 곳인가요?", f"공공데이터 기준 {len(lst)}곳입니다.")], [("홈", "/"), ("지역본부", "/hq/"), (h, path)]), "0.4")

def hub_hq():
    rows = [['<a href="/hq/%s/">%s</a>' % (sl(h), esc(h)), len(BY_HQ[h]), "{:,}".format(sum(a["hh"] for a in BY_HQ[h]))] for h in sorted(BY_HQ)]
    body = f"""
<div class="page-head"><h1>LH 지역본부별 단지</h1><p>14개 지역본부</p></div>
<p class="lead">LH 지역본부별 관할 단지를 정리했습니다. 본부를 누르면 관할 단지 목록을 볼 수 있습니다.</p>
{ad()}
{table(['지역본부', '단지', '세대'], rows, (1, 2))}
<p class="note">{NOTE}</p>
"""
    write("/hq/", layout("/hq/", "LH 지역본부별 관할 임대·분양 단지", "LH 지역본부별 관할 단지 수와 세대수.", body, [("LH 지역본부는 몇 개인가요?", f"공공데이터에 {len(BY_HQ)}개 본부가 있습니다.")], [("홈", "/"), ("지역본부", "/hq/")]), "0.5")
    for h in BY_HQ: page_hq(h)

def page_guide():
    items = [("영구임대", TYPE_DESC["영구임대"]), ("국민임대", TYPE_DESC["국민임대"]), ("행복주택", TYPE_DESC["행복주택"]), ("공공임대(5년·10년)", "일정 기간 임대 후 분양 전환이 가능한 임대주택입니다. 분양 전환 가격과 조건은 공고문을 확인하세요."), ("통합공공임대", TYPE_DESC["통합공공임대"]), ("매입임대", "LH가 기존 주택이나 신축 다세대주택을 사들여 임대하는 방식으로 단지 규모가 작고 여러 지역에 흩어져 있습니다.")]
    body = f"""
<div class="page-head"><h1>LH 임대주택 유형 안내 — 영구·국민·행복·공공임대 차이</h1><p>유형별 쉬운 설명</p></div>
<p class="lead">LH가 공급하는 임대주택 유형을 간단히 정리했습니다. 입주 자격(소득·자산·무주택 요건 등)과 임대료는 공고마다 다르므로 신청 전 마이홈포털(myhome.go.kr)과 LH청약플러스의 모집공고를 반드시 확인하세요.</p>
{ad()}
{''.join('<h2 class="group-title">%d. %s</h2><p class="lead">%s</p>' % (i + 1, t, d) for i, (t, d) in enumerate(items))}
<h2 class="group-title">신청은 어디서?</h2><p class="lead">모집공고는 LH청약플러스와 마이홈포털에 올라오며 공고문의 자격 요건을 확인한 뒤 온라인으로 신청합니다.</p>
<p class="note">{NOTE}</p>
{chips([("임대 유형", "/type/"), ("지역별", "/region/")])}
"""
    faq = [("영구임대와 국민임대의 차이는?", "영구임대는 생계·의료급여 수급자 등 저소득 취약계층, 국민임대는 소득·자산 요건을 갖춘 무주택 서민이 주된 대상입니다."), ("행복주택은 누구를 위한 주택인가요?", "청년·신혼부부·고령자 등 주거 취약계층을 위한 임대주택입니다.")]
    write("/guide/", layout("/guide/", "LH 임대주택 유형 안내 — 영구·국민·행복·공공임대 차이", "LH 영구임대·국민임대·행복주택·공공임대·매입임대 차이와 신청 방법 안내.", body, faq, [("홈", "/"), ("임대 유형 안내", "/guide/")]), "0.8")

def page_home():
    body = f"""
<div class="hero"><h1>🏘️ LH 임대·분양 단지 {len(A):,}곳 — 세대수·유형·준공일</h1><p>전국 LH 단지를 지역·유형별로 찾아보세요.</p></div>
{ad()}
<div class="card-grid">
<a class="card" href="/region/"><b>📍 지역별</b><span>시도·시군구 LH 단지</span></a>
<a class="card" href="/type/"><b>🏷️ 임대 유형</b><span>국민·영구·행복·공공</span></a>
<a class="card" href="/year/"><b>📅 준공연도</b><span>입주 시기로 찾기</span></a>
<a class="card" href="/rank/"><b>🏆 대단지 순위</b><span>세대수 TOP 100</span></a>
<a class="card" href="/hq/"><b>🏢 지역본부</b><span>14개 본부 관할</span></a>
<a class="card" href="/guide/"><b>📖 유형 안내</b><span>영구·국민·행복 차이</span></a>
</div>
<h2 class="group-title">🏆 세대수 많은 단지</h2>
{table(AH, [arow(a) for a in A[:10]])}
<p class="lead">우아임대는 한국토지주택공사(LH)의 전국 단지 공공데이터로 임대·분양 단지 {len(A):,}곳({stats(A)})의 유형·세대수·준공일·입주 시기를 정리한 사이트입니다. 입주 자격과 모집 일정은 담지 않으니 공고는 마이홈포털에서 확인하세요. 자세한 기준은 <a href="/about/">데이터 설명</a>을 참고하세요.</p>
"""
    faq = [("LH 단지 정보는 어디서 가져오나요?", "한국토지주택공사가 공공데이터포털에 공개한 ‘전국 LH아파트 단지 정보’를 사용합니다."), ("입주 신청은 어디서 하나요?", "마이홈포털과 LH청약플러스의 모집공고를 확인해 신청합니다.")]
    write("/", layout("/", f"우아임대 — LH 임대·분양 단지 {len(A):,}곳 세대수·유형·준공일", f"전국 LH 임대·분양 단지 {len(A):,}곳({stats(A)})을 지역·유형·준공연도별로 확인하세요. 국민임대·영구임대·행복주택 안내.", body, faq), "1.0")

def page_about():
    body = f"""
<div class="page-head"><h1>데이터 설명</h1><p>정보의 출처와 한계</p></div>
<h2 class="group-title">📚 출처</h2><p class="lead">한국토지주택공사 ‘전국 LH아파트 단지 정보’(공공데이터포털 15080989)를 사용했습니다. 단지코드, 단지명, 세대수, 동수, 임대유형, 주택유형, 주소, 준공일, 입주지정기간, 지역본부를 반영했고 주소가 없거나 세대수가 0인 항목, 기존주택 전세임대는 제외해 {len(A):,}곳을 담았습니다.</p>
<h2 class="group-title">⚠️ 한계</h2><p class="lead">{NOTE} 준공일이 비어 있는 단지는 입주 지정 시작 연도로 연도 분류를 했습니다. 임대료·입주 자격·모집 일정은 제공하지 않습니다.</p>
<h2 class="group-title">📬 문의·정정</h2><p class="lead">오류 제보는 <a href="mailto:ingmaster83@gmail.com">ingmaster83@gmail.com</a> 으로 보내 주세요.</p>
"""
    write("/about/", layout("/about/", "데이터 설명 — 출처와 한계", "우아임대 데이터 출처(한국토지주택공사 단지 정보)와 한계를 공개합니다.", body, None, [("홈", "/"), ("데이터 설명", "/about/")]), "0.5")

def page_privacy():
    body = """
<div class="page-head"><h1>개인정보처리방침</h1></div>
<p class="lead">우아임대(wooaimdae.wooahouse.com, 이하 “서비스”)는 회원가입·로그인을 요구하지 않으며 이용자의 개인정보를 직접 수집하지 않습니다.</p>
<h3>자동 수집 정보</h3><p class="lead">서비스 개선을 위해 Google Analytics로 방문자 수·페이지뷰 등 익명 통계를 수집하며, Google AdSense와 쿠팡 파트너스는 맞춤 광고를 위해 쿠키를 사용할 수 있습니다. 쿠키는 브라우저 설정에서 비활성화할 수 있습니다. (<a href="https://policies.google.com/privacy">Google 개인정보처리방침</a>, <a href="https://policies.google.com/technologies/ads">Google 광고 정책</a>)</p>
<h3>쿠팡 파트너스</h3><p class="lead">일부 페이지에는 쿠팡 파트너스 활동의 일환으로 광고가 포함되어 있으며 이에 따른 수수료를 제공받을 수 있습니다.</p>
<h3>문의</h3><p class="lead"><a href="mailto:ingmaster83@gmail.com">ingmaster83@gmail.com</a></p>
<p class="note">최종 수정일: 2026년 10월 25일</p>
"""
    write("/privacy/", layout("/privacy/", "개인정보처리방침", "우아임대 개인정보처리방침", body, None, [("홈", "/"), ("개인정보처리방침", "/privacy/")]), sitemap=False)

def make_og():
    f = ROOT / "assets" / "og-image.png"
    if f.exists(): return
    try: from PIL import Image, ImageDraw, ImageFont
    except Exception: return
    im = Image.new("RGB", (1200, 630), (21, 128, 61)); dr = ImageDraw.Draw(im)
    def font(sz):
        for n in ("malgunbd.ttf", "malgun.ttf", "NanumGothicBold.ttf"):
            try: return ImageFont.truetype(n, sz)
            except Exception: pass
        return ImageFont.load_default()
    dr.rounded_rectangle((90, 90, 1110, 540), 40, fill=(255, 255, 255))
    dr.text((150, 150), "우아임대", font=font(110), fill=(20, 83, 45))
    dr.text((150, 300), "LH 임대·분양 단지", font=font(54), fill=(31, 41, 55))
    dr.text((150, 380), "세대수 · 유형 · 준공일", font=font(54), fill=(31, 41, 55))
    dr.text((150, 470), "wooaimdae.wooahouse.com", font=font(34), fill=(107, 114, 128))
    im.save(f)

def main():
    t0 = time.time(); make_og()
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    for nf in ROOT.glob("naver*.html"): shutil.copy(nf, OUT / nf.name)
    for a in A: page_c(a)
    for s in SIDOS: page_sido(s)
    hub_region(); hub_type(); hub_year(); hub_hq()
    page_rank()
    for s in SIDOS: page_rank(s)
    page_guide(); page_home(); page_about(); page_privacy()
    today = time.strftime("%Y-%m-%d")
    urls = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (BASE, q(p), today, pr) for p, pr in WRITTEN)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls, encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE, encoding="utf-8")
    (OUT / "CNAME").write_text("wooaimdae.wooahouse.com\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    nf = layout("/404.html", "페이지를 찾을 수 없습니다", "요청한 페이지를 찾을 수 없습니다.", '<div class="page-head"><h1>페이지를 찾을 수 없습니다</h1></div><div class="chips"><a class="chip" href="/">홈</a><a class="chip" href="/region/">지역별 LH 단지</a></div>', None, None, noindex=True)
    (OUT / "404.html").write_text(nf, encoding="utf-8")
    print("pages", len(WRITTEN), "elapsed", round(time.time() - t0), "s")

if __name__ == "__main__":
    main()
