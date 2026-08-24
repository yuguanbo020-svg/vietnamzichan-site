#!/usr/bin/env python3
from __future__ import annotations
import html, json, re, sys, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/news_sources.json"
OUTPUT=ROOT/"data/news_multilingual.json"
MODEL="qwen3-coder:30b"
OLLAMA="http://127.0.0.1:11434/api/generate"
LANGS=("vi","zh","en")
CATEGORY={
"工业地产":{"vi":"Bất động sản công nghiệp","zh":"工业地产","en":"Industrial property"},
"投资观察":{"vi":"Theo dõi đầu tư","zh":"投资观察","en":"Investment watch"},
"政策解读":{"vi":"Phân tích chính sách","zh":"政策解读","en":"Policy brief"}}
DERIVED_NUMBERS={
"vietnam-fdi-first-seven-months-2026":{"12.9","5.6","986.2","0.9862"}}
FACT_TRANSLATIONS={
"bac-ninh-ngoc-chau-industrial-cluster-2026":{
"vi":["Lễ khởi công Cụm công nghiệp Ngọc Châu tại tỉnh Bắc Ninh diễn ra ngày 4 tháng 8 năm 2026.","Dự án có quy mô quy hoạch khoảng 75 ha và tổng vốn đầu tư gần 1 nghìn tỷ đồng.","Giai đoạn một đã hoàn tất giải phóng 35 ha mặt bằng; dự kiến hoàn thành xây dựng, nghiệm thu và đưa vào sử dụng trong năm 2027.","Quy hoạch hướng đến các ngành dệt may, dược phẩm, vật liệu, cơ khí, điện tử, ô tô, nội thất, công nghiệp hỗ trợ, cùng dịch vụ kho bãi và nhà xưởng."],
"en":["The groundbreaking ceremony for the Ngoc Chau Industrial Cluster in Bac Ninh Province took place on 4 August 2026.","The project has a planned area of about 75 hectares and total investment of nearly VND 1 trillion.","Land clearance for 35 hectares in the first phase has been completed; construction, acceptance and commissioning are planned for 2027.","The plan targets textiles, pharmaceuticals, materials, machinery, electronics, automotive, furniture and supporting industries, as well as warehouse and factory services."]},
"vietnam-fdi-first-seven-months-2026":{
"vi":["Trang thông tin chính thức dẫn số liệu của Tổng cục Thống kê Việt Nam cho biết vốn đầu tư trực tiếp nước ngoài liên quan vượt 12,9 tỷ USD tính đến ngày 20 tháng 7 năm 2026.","Trang này cho biết chỉ tiêu trên tăng 46,9% so với cùng kỳ.","Ngành chế biến, chế tạo thu hút khoảng 5,6 tỷ USD, chiếm 64,7% tổng vốn được đề cập.","Lĩnh vực bất động sản thu hút khoảng 986,2 triệu USD, chiếm 11,3%."],
"en":["The official page, citing Vietnam's General Statistics Office, said related foreign direct investment exceeded US$12.9 billion as of 20 July 2026.","The page said this measure increased 46.9% year on year.","Processing and manufacturing attracted about US$5.6 billion, accounting for 64.7% of the stated capital.","Real estate attracted about US$986.2 million, accounting for 11.3%."]},
"vietnam-investment-law-2025-effective-2026":{
"vi":["Luật Đầu tư năm 2025 của Việt Nam có hiệu lực từ ngày 1 tháng 3 năm 2026.","Bản tiếng Anh chính thức đề cập các dự án đầu tư trong khu công nghiệp, khu công nghệ cao và khu công nghệ số tập trung.","Văn bản luật cũng đề cập một số dự án đầu tư về công nghệ số, bán dẫn và trung tâm dữ liệu trí tuệ nhân tạo.","Điều kiện áp dụng cho từng dự án vẫn cần được đối chiếu theo địa điểm, ngành nghề và các quy định triển khai tiếp theo."],
"en":["Vietnam's 2025 Law on Investment took effect on 1 March 2026.","The official English text covers investment projects in industrial parks, high-tech parks and concentrated digital technology zones.","The law also covers certain investment projects involving digital technology, semiconductors and artificial-intelligence data centres.","The conditions applicable to a specific project still need to be checked against its location, industry and subsequent implementing rules."]}}
SOURCE_NAMES={"vi":{"越南政府新闻网":"Cổng Thông tin điện tử Chính phủ Việt Nam","河内高科技园官方英文信息":"Trang thông tin tiếng Anh của Khu Công nghệ cao Hòa Lạc","越南政府新闻网英文版":"Báo Điện tử Chính phủ Việt Nam — bản tiếng Anh"},"en":{"越南政府新闻网":"Vietnam Government News","河内高科技园官方英文信息":"Hoa Lac Hi-tech Park — official English information","越南政府新闻网英文版":"Viet Nam Government News — English edition"}}
EDITORIAL_REPLACEMENTS={
"bac-ninh-ngoc-chau-industrial-cluster-2026":{"10 nghìn tỷ":"1 nghìn tỷ","10万亿":"1万亿","100 billion VND":"1 trillion VND"},
"vietnam-fdi-first-seven-months-2026":{"56 tỷ USD":"5,6 tỷ USD","hơn 9 tỷ USD":"986,2 triệu USD","gần 10 tỷ USD":"khoảng 986,2 triệu USD","560亿美元":"56亿美元","超过9亿美元":"约9.862亿美元","近10亿美元":"约9.862亿美元","$56 billion":"$5.6 billion","over $9 billion":"about $986.2 million","nearly $10 billion":"about $986.2 million"}}

LABELS={
"vi":{"home":"Trang chủ","industrial":"Bất động sản công nghiệp","cities":"Thành phố","cooperation":"Cơ hội hợp tác","kicker":"TIN TỨC ĐẦU TƯ & CÔNG NGHIỆP VIỆT NAM","hero":"Thông tin đầu tư và công nghiệp Việt Nam","hero_p":"Tin tức có nguồn, tác động kinh doanh và các tín hiệu cần theo dõi cho doanh nghiệp Việt Nam và Trung Quốc.","edition":"Bản tin ngày 24/08/2026","facts":"Thông tin từ nguồn","impact":"Tác động kinh doanh","cross":"Ý nghĩa đối với hợp tác Việt–Trung","actions":"Điểm cần theo dõi","outlook":"Ba kịch bản","source":"Nguồn tham khảo","read":"Đọc phân tích","back":"Quay lại trung tâm tin tức","cta":"Bạn đang tìm nhà xưởng, đất công nghiệp hoặc cơ hội hợp tác tại Việt Nam?","cta_btn":"Gửi nhu cầu","model_note":"Nội dung phân tích được hỗ trợ bởi mô hình riêng tại Hà Nội và được trình bày tách biệt với thông tin nguồn."},
"zh":{"home":"首页","industrial":"工业地产","cities":"城市","cooperation":"合作机会","kicker":"越南投资与工业情报","hero":"越南投资与工业情报","hero_p":"提供可追溯新闻、商业影响和中越企业值得持续观察的市场信号。","edition":"2026年8月24日情报版","facts":"来源事实","impact":"商业影响","cross":"对中越企业的意义","actions":"值得继续观察","outlook":"三种情景","source":"参考来源","read":"阅读分析","back":"返回资讯中心","cta":"需要越南厂房、工业土地或合作机会？","cta_btn":"提交需求","model_note":"分析由河内本地私有模型辅助整理，并与来源事实分开呈现。"},
"en":{"home":"Home","industrial":"Industrial property","cities":"Cities","cooperation":"Cooperation","kicker":"VIETNAM INVESTMENT & INDUSTRY BRIEF","hero":"Vietnam investment and industry intelligence","hero_p":"Sourced developments, business implications and market signals for Vietnamese and Chinese companies.","edition":"24 August 2026 edition","facts":"Source facts","impact":"Business implications","cross":"What it means for Vietnam–China business","actions":"What to watch","outlook":"Three scenarios","source":"Reference source","read":"Read analysis","back":"Back to intelligence centre","cta":"Looking for factories, industrial land or partners in Vietnam?","cta_btn":"Submit a requirement","model_note":"Analysis is assisted by a private model running in Hanoi and is presented separately from sourced facts."}}

CSS=""":root{--ink:#10231d;--muted:#607069;--green:#063e34;--accent:#0a8068;--mint:#e8f5f0;--paper:#f4f7f5;--line:#dbe7e2;--gold:#c28d38}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}a{color:inherit}.wrap{width:min(1160px,calc(100% - 36px));margin:auto}.nav{background:#fff;border-bottom:1px solid var(--line)}.nav .wrap{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{font-size:22px;font-weight:850;color:var(--green);text-decoration:none}.links,.langs{display:flex;gap:18px}.links a,.langs a{text-decoration:none}.langs a{font-weight:800;color:var(--accent)}.hero{background:radial-gradient(circle at 83% 18%,#1b9c82 0,transparent 29%),linear-gradient(125deg,#052f29,#08715f);color:#fff;padding:68px 0}.hero h1{font-size:clamp(38px,5vw,60px);line-height:1.08;margin:10px 0 18px}.hero p{max-width:780px;color:#ddefe9;font-size:18px}.kicker,.tag{font-size:12px;font-weight:850;letter-spacing:.07em;text-transform:uppercase}.kicker{color:#bde6dc}.section{padding:48px 0}.section-head{display:flex;justify-content:space-between;align-items:end;gap:18px;margin-bottom:22px}.section-head h2{font-size:30px;margin:0}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.card{background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:0 8px 30px #073f3710}.card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}.card-body{padding:22px}.tag,.read{color:var(--accent);font-weight:800}.date{color:var(--muted);font-size:13px}.card h2{font-size:21px;line-height:1.35;margin:10px 0}.card p{color:var(--muted)}.read{text-decoration:none}.article{max-width:880px;margin:42px auto;background:#fff;border:1px solid var(--line);border-radius:20px;padding:clamp(24px,5vw,54px)}.article h1{font-size:clamp(34px,5vw,52px);line-height:1.15;margin:12px 0}.lead{font-size:20px;color:#42564e}.cover{width:100%;border-radius:16px;margin:22px 0}.panel{border-radius:14px;padding:20px;margin:24px 0;border:1px solid var(--line)}.facts{background:var(--mint)}.outlook{background:#092f28;color:#e9f7f3}.outlook h2{color:#fff}.source{background:#f7f4ec;border-color:#eadcc0}.article h2{margin-top:30px}.article li{margin:8px 0}.scenarios{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.scenario{background:#ffffff12;padding:14px;border-radius:10px}.cta{background:linear-gradient(120deg,#073f37,#0b7566);color:#fff;border-radius:18px;padding:30px;margin:40px 0}.btn{display:inline-block;background:#fff;color:var(--green);padding:10px 16px;border-radius:9px;text-decoration:none;font-weight:800}.note{font-size:13px;color:var(--muted);border-top:1px solid var(--line);margin-top:32px;padding-top:18px}.footer{background:#062e29;color:#c9ddd8;padding:35px 0;margin-top:50px}@media(max-width:820px){.grid,.scenarios{grid-template-columns:1fr}.links{display:none}.hero{padding:48px 0}.article{margin:20px 12px}.section-head{display:block}}"""

def esc(x): return html.escape(str(x),quote=True)
def clean(x,n):
    value=" ".join(str(x or "").split())
    if not value or len(value)>n: raise ValueError(f"invalid text length={len(value)}")
    return value
def ask(source):
    prompt="""You are the private editorial model for VietnamZiChan. Use ONLY verified_facts. Return strict JSON:
{"items":[{"slug":"","translations":{"vi":{"title":"","deck":"","impact":[],"cross_border":[],"watch":[],"base_case":"","upside_case":"","downside_case":"","seo_description":""},"zh":{same fields},"en":{same fields}}}]}
Facts will be rendered from locked translations, so do not return a facts field. Build decision-useful analysis from verified_facts only. Business impact must address demand, supply, operating cost, location choice or execution timing where supported. Vietnam-China meaning must identify a concrete decision for companies, not praise cooperation. Watch items must be observable signals. Each scenario must state a cause and business consequence. Avoid generic claims such as boosts development, attracts investors, creates jobs or supports exports unless tied to a specific mechanism in the facts. impact, cross_border and watch each require exactly 3 concise bullets. Scenarios are conditional interpretations, not factual claims. Do not mention AI, safety, experts, consensus, research shows, government strategy, or repeat caveats. Do not count list items or invent companies, locations, dates, percentages, money, areas or other numbers. Preserve every slug. Vietnamese must be natural Vietnamese, Chinese natural simplified Chinese, English natural business English. INPUT="""+json.dumps(source,ensure_ascii=False)
    body=json.dumps({"model":MODEL,"prompt":prompt,"stream":False,"format":"json","options":{"temperature":0.12,"num_ctx":12288,"num_predict":7500}},ensure_ascii=False).encode()
    req=urllib.request.Request(OLLAMA,data=body,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=900) as response:
        result=json.loads(json.loads(response.read())["response"])
    slug=source["items"][0]["slug"]
    Path(f"/tmp/vzc-news-draft-{slug}.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result
def repair_draft(slug,value):
    replacements=EDITORIAL_REPLACEMENTS.get(slug,{})
    if isinstance(value,dict): return {k:repair_draft(slug,v) for k,v in value.items()}
    if isinstance(value,list): return [repair_draft(slug,v) for v in value]
    if isinstance(value,str):
        for old,new in replacements.items(): value=value.replace(old,new)
    return value
def validate(source,generated):
    base={x["slug"]:x for x in source["items"]}; result=[]
    for row in generated.get("items",[]):
        slug=row.get("slug")
        if slug not in base: continue
        row=repair_draft(slug,row)
        item=dict(base.pop(slug)); translations={}
        for lang in LANGS:
            raw=row.get("translations",{}).get(lang,{})
            value={"title":clean(raw.get("title"),150),"deck":clean(raw.get("deck"),260),
             "facts":item["verified_facts"] if lang=="zh" else FACT_TRANSLATIONS[slug][lang],
             "impact":[clean(x,240) for x in raw.get("impact",[])],
             "cross_border":[clean(x,240) for x in raw.get("cross_border",[])],
             "watch":[clean(x,220) for x in raw.get("watch",[])],
             "base_case":clean(raw.get("base_case"),300),"upside_case":clean(raw.get("upside_case"),300),
             "downside_case":clean(raw.get("downside_case"),300),"seo_description":clean(raw.get("seo_description"),220)}
            if any(len(value[k])!=3 for k in ("impact","cross_border","watch")): raise ValueError("bullet count")
            combined=json.dumps(value,ensure_ascii=False).lower()
            if any(x in combined for x in ("ai团队","人工智能团队","安全","合规","专家认为","研究显示","industry consensus","experts believe","safety","nhóm ai","an toàn ai")): raise ValueError("editorial filler")
            number_tokens=lambda text:{x.replace(",",".") for x in re.findall(r"\d+(?:[.,]\d+)?",text)}
            source_numbers=number_tokens(json.dumps(item["verified_facts"],ensure_ascii=False))
            allowed=source_numbers|DERIVED_NUMBERS.get(item["slug"],set())
            analysis_only=dict(value); analysis_only.pop("facts")
            generated_numbers=number_tokens(json.dumps(analysis_only,ensure_ascii=False).lower())
            if generated_numbers-allowed: raise ValueError(f"invented number {sorted(generated_numbers-allowed)}")
            translations[lang]=value
        item["translations"]=translations; result.append(item)
    if base: raise ValueError("missing item")
    return {"edition_date":source["edition_date"],"model":MODEL,"items":result}
def path_for(lang,slug=None):
    root="" if lang=="vi" else f"/{lang}"
    return f"{root}/news/{slug}/" if slug else f"{root}/news/"
def section_path(lang,section=""):
    prefix=f"/{lang}" if lang in ("vi","zh","en") else ""
    return f"{prefix}/{section}/" if section else f"{prefix}/"
def nav(lang):
    l=LABELS[lang]
    return f'<div class="nav"><div class="wrap"><a class="brand" href="{section_path(lang)}">VietnamZiChan</a><div class="links"><a href="{section_path(lang)}">{l["home"]}</a><a href="{section_path(lang,"market")}">{l["industrial"]}</a><a href="{section_path(lang,"cities")}">{l["cities"]}</a><a href="{section_path(lang,"opportunities")}">{l["cooperation"]}</a></div><div class="langs"><a href="/news/">VI</a><a href="/zh/news/">中文</a><a href="/en/news/">EN</a></div></div></div>'
def bullets(items): return "".join(f"<li>{esc(x)}</li>" for x in items)
def article(item,lang):
    l=LABELS[lang]; t=item["translations"][lang]
    category=CATEGORY.get(item["category"],{}).get(lang,item["category"])
    source_name=SOURCE_NAMES.get(lang,{}).get(item["source_name"],item["source_name"])
    return f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(t["title"])} | VietnamZiChan</title><meta name="description" content="{esc(t["seo_description"])}"><link rel="canonical" href="https://vietnamzichan.com{path_for(lang,item["slug"])}"><style>{CSS}</style></head><body>{nav(lang)}<main class="article"><div class="tag">{esc(category)}</div><h1>{esc(t["title"])}</h1><div class="date">{esc(item["source_date"])}</div><p class="lead">{esc(t["deck"])}</p><img class="cover" src="{esc(item["image"])}" alt="{esc(t["title"])}"><section class="panel facts"><h2>{l["facts"]}</h2><ul>{bullets(t["facts"])}</ul></section><section><h2>{l["impact"]}</h2><ul>{bullets(t["impact"])}</ul></section><section><h2>{l["cross"]}</h2><ul>{bullets(t["cross_border"])}</ul></section><section><h2>{l["actions"]}</h2><ul>{bullets(t["watch"])}</ul></section><section class="panel outlook"><h2>{l["outlook"]}</h2><div class="scenarios"><div class="scenario"><strong>Base</strong><br>{esc(t["base_case"])}</div><div class="scenario"><strong>Upside</strong><br>{esc(t["upside_case"])}</div><div class="scenario"><strong>Downside</strong><br>{esc(t["downside_case"])}</div></div></section><section class="panel source"><strong>{l["source"]}：</strong><a href="{esc(item["source_url"])}" rel="nofollow noopener" target="_blank">{esc(source_name)}</a> · {esc(item["source_date"])}</section><section class="cta"><h2>{l["cta"]}</h2><a class="btn" href="{section_path(lang,"opportunities")}">{l["cta_btn"]}</a></section><p class="note">{l["model_note"]}</p><a class="read" href="{path_for(lang)}">← {l["back"]}</a></main><footer class="footer"><div class="wrap">VietnamZiChan</div></footer></body></html>'''
def index_page(data,lang):
    l=LABELS[lang]; cards=[]
    for item in data["items"]:
        t=item["translations"][lang]
        category=CATEGORY.get(item["category"],{}).get(lang,item["category"])
        cards.append(f'<article class="card"><img src="{esc(item["image"])}" alt="{esc(t["title"])}"><div class="card-body"><div class="tag">{esc(category)}</div><div class="date">{esc(item["source_date"])}</div><h2>{esc(t["title"])}</h2><p>{esc(t["deck"])}</p><a class="read" href="{path_for(lang,item["slug"])}">{l["read"]} →</a></div></article>')
    return f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{l["hero"]} | VietnamZiChan</title><meta name="description" content="{esc(l["hero_p"])}"><link rel="canonical" href="https://vietnamzichan.com{path_for(lang)}"><style>{CSS}</style></head><body>{nav(lang)}<section class="hero"><div class="wrap"><div class="kicker">{l["kicker"]}</div><h1>{l["hero"]}</h1><p>{l["hero_p"]}</p></div></section><main class="wrap section"><div class="section-head"><h2>{l["edition"]}</h2></div><section class="grid">{"".join(cards)}</section><section class="cta"><h2>{l["cta"]}</h2><a class="btn" href="{section_path(lang,"opportunities")}">{l["cta_btn"]}</a></section><p class="note">{l["model_note"]}</p></main><footer class="footer"><div class="wrap">VietnamZiChan</div></footer></body></html>'''
def write(data):
    for lang in LANGS:
        roots=[ROOT/"news"] if lang=="vi" else [ROOT/lang/"news"]
        if lang=="vi": roots.append(ROOT/"vi"/"news")
        for root in roots:
            root.mkdir(parents=True,exist_ok=True); (root/"index.html").write_text(index_page(data,lang),encoding="utf-8")
            for item in data["items"]:
                target=root/item["slug"]; target.mkdir(parents=True,exist_ok=True)
                (target/"index.html").write_text(article(item,lang),encoding="utf-8")
def main():
    source=json.loads(SOURCE.read_text(encoding="utf-8")); completed=[]
    for item in source["items"]:
        packet={"edition_date":source["edition_date"],"items":[item]}; last=None
        if "--from-drafts" in sys.argv:
            draft=Path(f"/tmp/vzc-news-draft-{item['slug']}.json")
            completed.extend(validate(packet,json.loads(draft.read_text(encoding="utf-8")))["items"])
            continue
        for _ in range(5):
            try:
                completed.extend(validate(packet,ask(packet))["items"])
                break
            except ValueError as exc:
                last=exc
                print(f"VALIDATION_RETRY={item['slug']}:{exc}",file=sys.stderr,flush=True)
        else: raise ValueError(f"validation failed for {item['slug']}: {last}")
    data={"edition_date":source["edition_date"],"model":MODEL,"items":completed}
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); write(data)
    print(json.dumps({"status":"PASS","model":MODEL,"languages":list(LANGS),"articles":len(data["items"])},ensure_ascii=False))
if __name__=="__main__": main()
