#!/usr/bin/env python3
from __future__ import annotations
import html, json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/news_sources.json"
OUTPUT = ROOT / "data/news_private_analysis.json"
MODEL = "qwen3-coder:30b"
OLLAMA = "http://127.0.0.1:11434/api/generate"

CSS = """
:root{--ink:#10231d;--muted:#607069;--green:#063e34;--accent:#0a8068;--mint:#e8f5f0;--paper:#f4f7f5;--line:#dbe7e2;--gold:#c28d38}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
a{color:inherit}.wrap{width:min(1160px,calc(100% - 36px));margin:auto}.nav{background:#fff;border-bottom:1px solid var(--line)}.nav .wrap{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:22px}.brand{font-size:22px;font-weight:850;color:var(--green);text-decoration:none}.links{display:flex;gap:22px}.links a{text-decoration:none}
.hero{background:radial-gradient(circle at 83% 18%,#1b9c82 0,transparent 29%),linear-gradient(125deg,#052f29,#08715f);color:#fff;padding:68px 0}.hero h1{font-size:clamp(38px,5vw,60px);line-height:1.08;margin:10px 0 18px}.hero p{max-width:780px;color:#ddefe9;font-size:18px}.kicker,.tag{font-size:12px;font-weight:850;letter-spacing:.07em;text-transform:uppercase}.kicker{color:#bde6dc}
.section{padding:48px 0}.section-head{display:flex;justify-content:space-between;align-items:end;gap:18px;margin-bottom:22px}.section-head h2{font-size:30px;margin:0}.section-head p{color:var(--muted);margin:4px 0}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.card{background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:0 8px 30px #073f3710}.card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}.card-body{padding:22px}.tag{color:var(--accent)}.date{color:var(--muted);font-size:13px}.card h2{font-size:21px;line-height:1.35;margin:10px 0}.card p{color:var(--muted)}.read{color:var(--accent);font-weight:800;text-decoration:none}
.article{max-width:860px;margin:42px auto;background:#fff;border:1px solid var(--line);border-radius:20px;padding:clamp(24px,5vw,54px)}.article h1{font-size:clamp(34px,5vw,52px);line-height:1.15;margin:12px 0}.lead{font-size:20px;color:#42564e}.cover{width:100%;border-radius:16px;margin:22px 0}.factbox,.source,.forecast,.discussion{border-radius:14px;padding:20px;margin:24px 0}.factbox{background:var(--mint)}.source{background:#f7f4ec;border:1px solid #eadcc0}.discussion{border:1px solid var(--line)}.forecast{background:#092f28;color:#e9f7f3}.forecast strong{color:#fff}.article h2{margin-top:34px}.article li{margin:8px 0}.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{background:var(--mint);color:var(--green);padding:6px 10px;border-radius:999px;font-size:13px}.cta{background:linear-gradient(120deg,#073f37,#0b7566);color:#fff;border-radius:18px;padding:30px;margin:40px 0}.btn{display:inline-block;background:#fff;color:var(--green);padding:10px 16px;border-radius:9px;text-decoration:none;font-weight:800}.footer{background:#062e29;color:#c9ddd8;padding:35px 0;margin-top:50px}
@media(max-width:820px){.grid{grid-template-columns:1fr}.links{display:none}.hero{padding:48px 0}.article{margin:20px 12px}.section-head{display:block}}
"""

def esc(value): return html.escape(str(value), quote=True)
def clean(value, limit):
    text=" ".join(str(value or "").split())
    if not text or len(text)>limit: raise ValueError("invalid generated text")
    return text

def ask_private_model(source):
    prompt = """你是VietnamZiChan本地私有分析团队。只根据INPUT中的verified_facts写中文商业情报，禁止增加任何数字、公司、地点、日期或事件事实。
严格返回JSON：{"items":[{"slug":"","title":"","summary":"","analysis":"","discussion":{"research":"","market":"","risk":"","consensus":""},"forecast":{"horizon":"","confidence":"","prediction":"","invalidators":[]},"seo_description":""}]}
规则：每个slug必须原样保留；summary<=110字；analysis<=420字；四个讨论角色每项<=150字；预测必须明确是推演而非事实，confidence只能低或中，invalidators 2至4项；标题自然包含主题关键词但不能堆砌；不得复制来源长句。
禁止写“研究显示、专家认为、业界认为、市场普遍认为、政府战略、政府支持加强、政策持续支持、政策调控导致”等INPUT未提供的外部背书或因果关系；团队讨论只能写成“本团队从资料/市场/风险角度推测”，并使用“可能、仍需验证、不能据此确认”等边界词。不得把一月至七月写成上半年。预测不得增加INPUT没有出现的资金、面积、比例、年份或其他数字。INPUT=
""" + json.dumps(source, ensure_ascii=False)
    body=json.dumps({"model":MODEL,"prompt":prompt,"stream":False,"format":"json",
                     "options":{"temperature":0.15,"num_ctx":8192,"num_predict":4500}},ensure_ascii=False).encode()
    req=urllib.request.Request(OLLAMA,data=body,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=900) as response:
        result=json.loads(response.read())
    return json.loads(result["response"])

def validate(source, generated):
    by_slug={item["slug"]:item for item in source["items"]}
    output=[]
    for item in generated.get("items",[]):
        slug=item.get("slug")
        if slug not in by_slug: continue
        base=dict(by_slug.pop(slug)); discussion=item.get("discussion",{}); forecast=item.get("forecast",{})
        base.update({"title":clean(item.get("title"),120),"summary":clean(item.get("summary"),180),
          "analysis":clean(item.get("analysis"),700),"seo_description":clean(item.get("seo_description"),180),
          "discussion":{k:clean(discussion.get(k),260) for k in ("research","market","risk","consensus")},
          "forecast":{"horizon":clean(forecast.get("horizon"),80),"confidence":forecast.get("confidence"),
          "prediction":clean(forecast.get("prediction"),300),
          "invalidators":[clean(x,120) for x in forecast.get("invalidators",[])[:4]]}})
        combined=json.dumps(base,ensure_ascii=False)
        forbidden=("研究显示","专家认为","业界普遍","多数专家","政府支持持续加强",
                   "政策支持和劳动力成本","政府推动","战略方向","政策调控影响",
                   "提供法律支持","将提升越南","明确支持")
        if any(term in combined for term in forbidden):
            raise ValueError("unverified authority claim")
        source_numbers=set(re.findall(r"\d+(?:\.\d+)?",json.dumps(base["verified_facts"],ensure_ascii=False)))
        generated_claims=" ".join([base["title"],base["summary"],base["analysis"],
            *base["discussion"].values(),base["forecast"]["prediction"],base["seo_description"]])
        novel_numbers=set(re.findall(r"\d+(?:\.\d+)?",generated_claims))-source_numbers
        if novel_numbers:
            raise ValueError("novel numeric claim:" + ",".join(sorted(novel_numbers)))
        if base["forecast"]["confidence"] not in {"低","中"} or len(base["forecast"]["invalidators"])<2:
            raise ValueError("invalid forecast")
        output.append(base)
    if by_slug: raise ValueError("missing slugs")
    return {"edition_date":source["edition_date"],"model":MODEL,"items":output}

def nav():
    return '<div class="nav"><div class="wrap"><a class="brand" href="/">VietnamZiChan</a><div class="links"><a href="/">首页</a><a href="/industrial-property/">工业地产</a><a href="/cities/">城市</a><a href="/cooperation/">合作机会</a></div></div></div>'

def render_article(item):
    facts="".join(f"<li>{esc(x)}</li>" for x in item["verified_facts"])
    invalid="".join(f"<li>{esc(x)}</li>" for x in item["forecast"]["invalidators"])
    chips="".join(f'<span class="chip">{esc(x)}</span>' for x in item["keywords"])
    d=item["discussion"]; f=item["forecast"]
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(item["title"])} | VietnamZiChan</title><meta name="description" content="{esc(item["seo_description"])}"><link rel="canonical" href="https://vietnamzichan.com/news/{esc(item["slug"])}/"><style>{CSS}</style></head><body>{nav()}<main class="article"><div class="tag">{esc(item["category"])}</div><h1>{esc(item["title"])}</h1><div class="date">本期整理：2026-08-24 · 原始来源日期：{esc(item["source_date"])}</div><p class="lead">{esc(item["summary"])}</p><img class="cover" src="{esc(item["image"])}" alt="{esc(item["title"])}主题示意图"><div class="chips">{chips}</div><section class="factbox"><h2>来源事实</h2><ul>{facts}</ul></section><h2>VietnamZiChan 分析</h2><p>{esc(item["analysis"])}</p><section class="discussion"><h2>本地AI团队讨论</h2><p><strong>资料研究：</strong>{esc(d["research"])}</p><p><strong>市场观察：</strong>{esc(d["market"])}</p><p><strong>风险审阅：</strong>{esc(d["risk"])}</p><p><strong>综合判断：</strong>{esc(d["consensus"])}</p></section><section class="forecast"><h2>情景推演（不是事实）</h2><p><strong>观察周期：</strong>{esc(f["horizon"])}　<strong>置信程度：</strong>{esc(f["confidence"])}</p><p>{esc(f["prediction"])}</p><strong>以下情况可能使推演失效：</strong><ul>{invalid}</ul></section><section class="source"><strong>参考来源：</strong><a href="{esc(item["source_url"])}" rel="nofollow noopener" target="_blank">{esc(item["source_name"])}</a>，发布于 {esc(item["source_date"])}。本文为独立整理与分析，不是对原文的转载。</section><section class="cta"><h2>需要越南厂房、土地、仓库或投资合作信息？</h2><p>提交具体城市、面积、用途和时间要求，我们据此整理可核验的信息。</p><a class="btn" href="/cooperation/">提交需求</a></section><a class="read" href="/news/">← 返回资讯中心</a></main><footer class="footer"><div class="wrap">VietnamZiChan · 越南资产与投资情报</div></footer></body></html>'''

def render_index(data):
    cards=[]
    for item in data["items"]:
        cards.append(f'''<article class="card"><img src="{esc(item["image"])}" alt="{esc(item["title"])}主题示意图"><div class="card-body"><div class="tag">{esc(item["category"])}</div><div class="date">{esc(item["source_date"])} · 来源可追溯</div><h2>{esc(item["title"])}</h2><p>{esc(item["summary"])}</p><a class="read" href="/news/{esc(item["slug"])}/">查看事实、讨论与推演 →</a></div></article>''')
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>越南投资、工业地产与中越贸易资讯 | VietnamZiChan</title><meta name="description" content="VietnamZiChan整理越南投资、工业地产、厂房、工业土地与中越贸易公开信息，并提供本地AI团队讨论和标注边界的情景推演。"><link rel="canonical" href="https://vietnamzichan.com/news/"><style>{CSS}</style></head><body>{nav()}<section class="hero"><div class="wrap"><div class="kicker">VIETNAM ASSET INTELLIGENCE</div><h1>越南投资与工业地产情报</h1><p>参考可追溯的公开信息，由河内本地私有模型完成摘要、交叉视角讨论和情景推演。事实、观点与预测分别标注，不把模型判断包装成新闻。</p></div></section><main class="wrap section"><div class="section-head"><div><h2>2026年8月24日情报版</h2><p>关注越南工业地产、制造业投资、政策与中越合作线索。</p></div><div class="date">图片为站内原创主题示意图</div></div><section class="grid">{''.join(cards)}</section><section class="cta"><h2>把资讯变成可执行的越南需求</h2><p>告诉我们目标城市、资产类型或合作方向，进入可核验的信息整理流程。</p><a class="btn" href="/cooperation/">提交需求</a></section></main><footer class="footer"><div class="wrap">VietnamZiChan · 事实来源、AI讨论与情景推演分层呈现</div></footer></body></html>'''

def main():
    source=json.loads(SOURCE.read_text(encoding="utf-8"))
    last_error=None
    for _ in range(3):
        try:
            data=validate(source,ask_private_model(source))
            break
        except ValueError as exc:
            last_error=exc
    else:
        raise ValueError(f"private model failed validation after 3 attempts: {last_error}")
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"news/index.html").write_text(render_index(data),encoding="utf-8")
    for item in data["items"]:
        target=ROOT/"news"/item["slug"]; target.mkdir(parents=True,exist_ok=True)
        (target/"index.html").write_text(render_article(item),encoding="utf-8")
    sitemap=ROOT/"sitemap.xml"
    if sitemap.is_file():
        text=sitemap.read_text(encoding="utf-8")
        additions=[]
        for item in data["items"]:
            url=f"https://vietnamzichan.com/news/{item['slug']}/"
            if url not in text:
                additions.append(f"<url><loc>{url}</loc><lastmod>{data['edition_date']}</lastmod></url>")
        if additions:
            sitemap.write_text(text.replace("</urlset>","".join(additions)+"</urlset>"),encoding="utf-8")
    print(json.dumps({"status":"PASS","model":MODEL,"articles":len(data["items"]),"output":str(OUTPUT)},ensure_ascii=False))
    return 0
if __name__=="__main__": raise SystemExit(main())
