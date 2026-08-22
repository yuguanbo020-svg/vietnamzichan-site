#!/usr/bin/env python3
"""Build portal translations and static pages across vi, zh, en without touching sitemap.xml."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://vietnamzichan.com"

CATEGORIES = {
    "factory": (
        ("厂房", "Factory", "Nhà xưởng", "现成厂房、园区厂房与制造业选址"),
        ("Factory", "Factory", "Nhà xưởng", "Ready-built factories, industrial park plants and manufacturing site selection"),
        ("Nhà xưởng", "Factory", "Nhà xưởng", "Nhà xưởng xây sẵn, nhà máy trong khu công nghiệp và tư vấn vị trí sản xuất"),
    ),
    "industrial-land": (
        ("工业土地", "Industrial land", "Đất công nghiệp", "工业园土地、长期租赁与项目落地"),
        ("Industrial Land", "Industrial land", "Đất công nghiệp", "Industrial park land, long-term leases and project deployment"),
        ("Đất công nghiệp", "Industrial land", "Đất công nghiệp", "Đất khu công nghiệp, thuê đất dài hạn và triển khai dự án"),
    ),
    "warehouse": (
        ("仓库物流", "Warehouse & logistics", "Kho vận", "仓储、配送中心与供应链节点"),
        ("Warehouse & Logistics", "Warehouse & logistics", "Kho vận", "Warehousing, distribution centers and supply chain nodes"),
        ("Kho vận & Logistics", "Warehouse & logistics", "Kho vận", "Kho bãi, trung tâm phân phối và điểm tựa chuỗi cung ứng"),
    ),
    "hotel": (
        ("酒店商业", "Hotel & commercial", "Khách sạn & thương mại", "酒店、商铺及收益型商业资产"),
        ("Hotel & Commercial", "Hotel & commercial", "Khách sạn & thương mại", "Hotels, retail shops and income-producing commercial assets"),
        ("Khách sạn & Thương mại", "Hotel & commercial", "Khách sạn & thương mại", "Khách sạn, cửa hàng bán lẻ và tài sản thương mại sinh lời"),
    ),
    "residential": (
        ("住宅公寓", "Residential", "Nhà ở", "住宅、公寓与服务式公寓"),
        ("Residential", "Residential", "Nhà ở", "Residential housing, apartments and serviced residences"),
        ("Nhà ở & Căn hộ", "Residential", "Nhà ở", "Nhà ở, căn hộ và căn hộ dịch vụ"),
    ),
    "agriculture": (
        ("农业资产", "Agricultural assets", "Tài sản nông nghiệp", "农场、果园及农业合作"),
        ("Agricultural Assets", "Agricultural assets", "Tài sản nông nghiệp", "Farms, orchards and agricultural cooperation"),
        ("Tài sản nông nghiệp", "Agricultural assets", "Tài sản nông nghiệp", "Nông trang, vườn cây ăn quả và hợp tác nông nghiệp"),
    ),
}

CITIES = {
    "ho-chi-minh-city": (
        ("胡志明市", "Ho Chi Minh City", "TP. Hồ Chí Minh", "消费、金融与南部供应链中心"),
        ("Ho Chi Minh City", "Ho Chi Minh City", "TP. Hồ Chí Minh", "Consumption, finance and southern supply chain hub"),
        ("TP. Hồ Chí Minh", "Ho Chi Minh City", "TP. Hồ Chí Minh", "Trung tâm tiêu thụ, tài chính và chuỗi cung ứng miền Nam"),
    ),
    "binh-duong": (
        ("平阳", "Binh Duong", "Bình Dương", "成熟工业园集群与制造业走廊"),
        ("Binh Duong", "Binh Duong", "Bình Dương", "Mature industrial park clusters and manufacturing corridor"),
        ("Bình Dương", "Binh Duong", "Bình Dương", "Cụm khu công nghiệp phát triển và hành lang sản xuất"),
    ),
    "dong-nai": (
        ("同奈", "Dong Nai", "Đồng Nai", "港口、机场与南部制造业节点"),
        ("Dong Nai", "Dong Nai", "Đồng Nai", "Ports, airports and southern manufacturing node"),
        ("Đồng Nai", "Dong Nai", "Đồng Nai", "Cảng biển, sân bay và điểm tựa sản xuất miền Nam"),
    ),
    "hanoi": (
        ("河内", "Hanoi", "Hà Nội", "北部总部、服务业与产业协同中心"),
        ("Hanoi", "Hanoi", "Hà Nội", "Northern headquarters, services and industrial synergy hub"),
        ("Hà Nội", "Hanoi", "Hà Nội", "Trung tâm trụ sở miền Bắc, dịch vụ và hội tụ công nghiệp"),
    ),
    "bac-ninh": (
        ("北宁", "Bac Ninh", "Bắc Ninh", "电子制造与北部产业链核心"),
        ("Bac Ninh", "Bac Ninh", "Bắc Ninh", "Electronics manufacturing and northern supply chain core"),
        ("Bắc Ninh", "Bac Ninh", "Bắc Ninh", "Trung tâm sản xuất điện tử và chuỗi cung ứng miền Bắc"),
    ),
    "hai-phong": (
        ("海防", "Hai Phong", "Hải Phòng", "深水港、出口制造与物流门户"),
        ("Hai Phong", "Hai Phong", "Hải Phòng", "Deep-water ports, export manufacturing and logistics gateway"),
        ("Hải Phòng", "Hai Phong", "Hải Phòng", "Cảng nước sâu, sản xuất xuất khẩu và cửa ngõ logistics"),
    ),
    "da-nang": (
        ("岘港", "Da Nang", "Đà Nẵng", "中部服务业、旅游与科技节点"),
        ("Da Nang", "Da Nang", "Đà Nẵng", "Central services, tourism and technology node"),
        ("Đà Nẵng", "Da Nang", "Đà Nẵng", "Trung tâm dịch vụ, du lịch và công nghệ miền Trung"),
    ),
}

LANGS = {
    "vi": ("vi-VN", "Tiếng Việt"),
    "zh": ("zh-CN", "中文"),
    "en": ("en", "English"),
}

SEO_TYPES = {
    "factory-for-rent": (
        ("厂房出租", "Nhà xưởng cho thuê", "factory", "现成厂房、生产厂房、园区标准厂房", "nhà xưởng xây sẵn, nhà máy sản xuất, xưởng trong khu công nghiệp"),
        ("Factory for Rent", "Factory for rent", "factory", "Ready-built factories, production plants and industrial park workshops", "nhà xưởng xây sẵn, nhà máy sản xuất, xưởng trong khu công nghiệp"),
        ("Nhà xưởng cho thuê", "Factory for rent", "factory", "Nhà xưởng xây sẵn, nhà máy sản xuất và xưởng tiêu chuẩn trong khu công nghiệp", "nhà xưởng xây sẵn, nhà máy sản xuất, xưởng trong khu công nghiệp"),
    ),
    "industrial-land": (
        ("工业土地", "Đất công nghiệp", "industrial-land", "工业园土地、长期租赁、制造业项目用地", "đất khu công nghiệp, thuê đất dài hạn, địa điểm dự án sản xuất"),
        ("Industrial Land", "Industrial land", "industrial-land", "Industrial park land, long-term leases and manufacturing project sites", "đất khu công nghiệp, thuê đất dài hạn, địa điểm dự án sản xuất"),
        ("Đất công nghiệp", "Industrial land", "industrial-land", "Đất khu công nghiệp, thuê đất dài hạn và địa điểm cho dự án sản xuất", "đất khu công nghiệp, thuê đất dài hạn, địa điểm dự án sản xuất"),
    ),
    "warehouse-for-rent": (
        ("仓库出租", "Kho cho thuê", "warehouse", "物流仓库、保税仓、配送中心与厂区仓储", "kho logistics, trung tâm phân phối, kho trong khu công nghiệp"),
        ("Warehouse for Rent", "Warehouse for rent", "warehouse", "Logistics warehouses, bonded warehouses, distribution centers and plant storage", "kho logistics, trung tâm phân phối, kho trong khu công nghiệp"),
        ("Kho cho thuê", "Warehouse for rent", "warehouse", "Kho logistics, kho ngoại quan, trung tâm phân phối và kho bãi nhà máy", "kho logistics, trung tâm phân phối, kho trong khu công nghiệp"),
    ),
}

CSS = r'''
:root{--ink:#12221f;--muted:#63716d;--green:#073f37;--green2:#0b7566;--mint:#e9f5f1;--gold:#c69442;--paper:#f7f9f8;--white:#fff;--line:#dce6e2}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit;text-decoration:none}.wrap{width:min(1160px,calc(100% - 36px));margin:auto}.top{background:#052f2a;color:#d9eae6;font-size:13px}.top .wrap,.nav{display:flex;align-items:center;justify-content:space-between;gap:18px}.top .wrap{min-height:34px}.lang a{margin-left:12px}.nav{min-height:72px}.nav-shell{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:30}.brand{font-size:21px;font-weight:850;color:var(--green);line-height:1.1}.brand small{display:block;color:var(--muted);font-size:11px;font-weight:600}.links{display:flex;gap:22px;font-size:14px}.action,.btn{display:inline-flex;align-items:center;justify-content:center;background:var(--green);color:#fff;border-radius:10px;padding:11px 17px;font-weight:750;border:0;cursor:pointer}.hero{color:#fff;background:radial-gradient(circle at 80% 25%,#178c78 0,transparent 34%),linear-gradient(120deg,#052f2a,#086458);padding:68px 0 58px}.hero-grid{display:grid;grid-template-columns:1.35fr .65fr;gap:42px}.kicker{color:#b8e1d8;font-size:13px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.hero h1{font-size:clamp(38px,5vw,62px);line-height:1.05;letter-spacing:-.035em;margin:14px 0 18px}.hero p{font-size:18px;color:#e1efec;max-width:720px}.search{display:grid;grid-template-columns:1fr 180px auto;background:#fff;padding:8px;border-radius:14px;margin-top:28px;box-shadow:0 18px 45px #001b1640}.search input,.search select{border:0;padding:12px;background:#fff;min-width:0}.search input{border-right:1px solid var(--line)}.proof{align-self:end;background:#ffffff13;border:1px solid #ffffff2c;border-radius:18px;padding:24px}.proof b{display:block;font-size:30px}.proof div+div{border-top:1px solid #ffffff24;margin-top:15px;padding-top:15px}.section{padding:54px 0}.head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:22px}.head h2{font-size:30px;line-height:1.2;margin:0}.head p{margin:7px 0 0;color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px;transition:.2s}.card:hover{transform:translateY(-3px);border-color:#a9cdc5;box-shadow:0 12px 30px #0b4e4010}.card .arrow{color:var(--green2);font-weight:800}.card h3{margin:10px 0 6px;font-size:20px}.card p{color:var(--muted);margin:0}.eyebrow{font-size:12px;color:var(--green2);font-weight:800;text-transform:uppercase}.industrial{background:var(--green);color:#fff}.industrial p{color:#c9ded9}.industrial .card{background:#ffffff0d;border-color:#ffffff24}.industrial .card p{color:#c9ded9}.industrial .arrow{color:#aee2d7}.chips{display:flex;flex-wrap:wrap;gap:10px}.chip{padding:9px 13px;background:#fff;border:1px solid var(--line);border-radius:999px;font-size:14px}.listing-layout{display:grid;grid-template-columns:260px 1fr;gap:22px}.filters{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;height:max-content}.filters label{display:block;font-size:13px;font-weight:800;margin:12px 0 5px}.filters input,.filters select,.form input,.form select,.form textarea{width:100%;border:1px solid var(--line);border-radius:9px;padding:11px;background:#fff}.empty{background:#fff;border:1px dashed #afc6c0;border-radius:16px;padding:44px;text-align:center}.empty h3{margin-top:0}.notice{background:#fff7e7;border:1px solid #ead3a7;border-radius:12px;padding:14px;color:#70521e}.steps{counter-reset:s}.step:before{counter-increment:s;content:counter(s);display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--mint);color:var(--green);font-weight:850}.cta{display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center;background:linear-gradient(120deg,#073f37,#0b7566);color:#fff;border-radius:20px;padding:34px}.cta h2{margin:0}.cta p{color:#d9ece7}.cta .btn{background:#fff;color:var(--green)}.form{max-width:820px;background:#fff;border:1px solid var(--line);border-radius:18px;padding:26px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}.form label{font-size:13px;font-weight:800}.form textarea{min-height:130px}.full{grid-column:1/-1}.footer{background:#062e29;color:#c5d9d5;margin-top:55px;padding:42px 0 25px}.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:28px}.footer h3{color:#fff}.footer a{display:block;margin:7px 0}.fine{border-top:1px solid #ffffff1e;margin-top:28px;padding-top:18px;font-size:12px}.breadcrumb{font-size:13px;color:var(--muted);margin:22px 0}.page-hero{background:#eaf4f1;padding:46px 0}.page-hero h1{font-size:42px;line-height:1.1;margin:8px 0}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:24px}.fact{background:#fff;border-radius:12px;padding:16px}.faq details{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:10px 0}.faq summary{font-weight:800;cursor:pointer}.mobile-menu{display:none}@media(max-width:850px){.links{display:none}.hero-grid,.listing-layout{grid-template-columns:1fr}.proof{display:none}.grid{grid-template-columns:repeat(2,1fr)}.hero{padding:48px 0}.search{grid-template-columns:1fr}.search input{border-right:0;border-bottom:1px solid var(--line)}.facts{grid-template-columns:1fr}.mobile-menu{display:block}.footer-grid{grid-template-columns:1fr 1fr}}@media(max-width:560px){.grid,.form-grid,.footer-grid{grid-template-columns:1fr}.cta{grid-template-columns:1fr}.section{padding:40px 0}.page-hero h1{font-size:34px}.top .wrap>span{display:none}.hero h1{font-size:40px}}
'''

JS = r'''
const form=document.querySelector('[data-search]');if(form){form.addEventListener('submit',e=>{e.preventDefault();const q=form.querySelector('[name=q]').value.trim(),city=form.querySelector('[name=city]').value,lang=document.documentElement.lang.slice(0,2);location.href='/'+lang+'/listings/?q='+encodeURIComponent(q)+'&city='+encodeURIComponent(city)})}const list=document.querySelector('[data-list]');if(list){const p=new URLSearchParams(location.search),q=(p.get('q')||'').toLowerCase(),city=(p.get('city')||'').toLowerCase();document.querySelectorAll('[data-filter-field]').forEach(x=>{if(p.has(x.name))x.value=p.get(x.name)});fetch('/data/listings.json').then(r=>r.json()).then(d=>{let xs=(d.items||[]).filter(x=>x.publish_status==='published');xs=xs.filter(x=>!q||JSON.stringify(x).toLowerCase().includes(q)).filter(x=>!city||JSON.stringify(x).toLowerCase().includes(city));const count=document.querySelector('[data-count]');if(count)count.textContent=String(xs.length);if(!xs.length)return;list.innerHTML=xs.map(x=>`<article class="card"><span class="eyebrow">${esc(x.city_region||'Việt Nam')} · ${esc(x.category||'Tài sản')}</span><h3>${esc(x.title||x.title_zh)}</h3><p>${esc(x.summary||x.summary_zh)}</p></article>`).join('')}).catch(()=>{});}function esc(v){return String(v||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function slug(v){return String(v||'item').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'item'}
'''

UI = {
    "vi": {
        "top_info": "Thông tin bất động sản Việt Nam · Lưu giữ nguồn gốc · Xác minh trước khi giao dịch",
        "brand_sub": "Cổng thông tin tài sản Việt Nam",
        "nav": ("BĐS công nghiệp", "Khu vực", "Danh sách", "Hợp tác", "Tin cậy", "Liên hệ"),
        "footer_desc": "Cổng thông tin khám phá bất động sản công nghiệp, tài sản thương mại và hợp tác xuyên biên giới tại Việt Nam. Lưu giữ nguồn gốc và đối chiếu kỹ lưỡng trước mọi quyết định.",
        "assets_title": "Tài sản",
        "services_title": "Dịch vụ",
        "asset_links": [("Nhà xưởng", "/vi/categories/factory/"), ("Đất công nghiệp", "/vi/categories/industrial-land/"), ("Kho vận", "/vi/categories/warehouse/")],
        "service_links": [("Tìm kiếm & Lọc", "/vi/listings/"), ("Gửi yêu cầu", "/vi/listings/"), ("Nguyên tắc tin cậy", "/vi/trust/")],
        "disclaimer": "Thông tin công khai không phải là lời khuyên pháp lý, đầu tư hay tài chính. Giá cả, quyền sở hữu, tình trạng sẵn có và điều kiện hợp tác cần được xác minh trực tiếp với chủ sở hữu và chuyên gia tư vấn.",
        "search_ph": "Tìm nhà xưởng, đất, kho hoặc cơ hội hợp tác",
        "city_ph": "Tất cả các tỉnh thành trọng điểm",
        "search_btn": "Tìm kiếm",
        "home_title": "Tài sản Việt Nam, từ tìm kiếm đến xác minh",
        "home_desc": "Khám phá nhà xưởng, đất công nghiệp, kho vận, khách sạn và cơ hội hợp tác với nguồn thông tin minh bạch và quy trình tư vấn chuyên nghiệp.",
        "hero_kicker": "Bất động sản công nghiệp · Tài sản thương mại · Hợp tác",
        "proof": [("6 loại", "Danh mục cốt lõi"), ("7 tỉnh", "Thành phố công nghiệp"), ("100%", "Giữ nguồn & trạng thái")],
        "sec1_title": "Khám phá theo loại tài sản",
        "sec1_desc": "Được tổ chức theo nhu cầu thực tế của nhà đầu tư, không có nội dung rườm rà.",
        "sec2_title": "Trọng tâm bất động sản công nghiệp",
        "sec2_desc": "Địa điểm sản xuất, nhà xưởng xây sẵn, đất khu công nghiệp và kho vận logistics.",
        "sec3_title": "Khu vực và hành lang kinh tế trọng điểm",
        "sec3_desc": "Chuyên trang tỉnh thành hỗ trợ so sánh khu vực, tiêu chuẩn kỹ thuật và cập nhật thông tin.",
        "cta_home_title": "Bạn đang tìm kiếm tài sản nào tại Việt Nam?",
        "cta_home_desc": "Gửi thông tin về tỉnh thành, diện tích, ngân sách, mục đích sử dụng và lịch trình. Hệ thống sẽ kết nối với đội ngũ tư vấn chuyên sâu.",
        "cta_home_btn": "Gửi yêu cầu ngay",
        "market_title": "Nhu cầu bất động sản công nghiệp nổi bật",
        "market_text": "Xem nhanh các từ khóa theo tỉnh thành và loại tài sản để gửi yêu cầu kết nối nhanh chóng.",
        "market_cta": "Xem từ khóa theo khu vực",
        "home_seo_title": "Bất động sản công nghiệp Việt Nam | Nhà xưởng & Đất kho",
        "home_seo_desc": "Cổng thông tin tìm kiếm nhà xưởng, đất công nghiệp, kho vận và cơ hội hợp tác tại Việt Nam với nguồn gốc được lưu giữ và quy trình xác minh chuyên nghiệp.",
        "breadcrumb_home": "Trang chủ",
        "read_more": "Xem chi tiết →",
        "faq_heading": "Câu hỏi thường gặp",
        "faq1_q": "Thông tin tài sản đã được xác minh chưa?",
        "faq1_a": "Trang web chỉ hiển thị các thông tin công khai đã qua kiểm duyệt sơ bộ và lưu giữ nguồn gốc. Giá cả, pháp lý và tình trạng thực tế cần được đối chiếu lại trước khi giao dịch.",
        "faq2_q": "Làm thế nào để gửi yêu cầu cụ thể?",
        "faq2_a": "Vui lòng điền biểu mẫu liên hệ với các tiêu chí về địa điểm, diện tích, ngân sách và mục đích. Chuyên viên của chúng tôi sẽ hỗ trợ xác minh và kết nối.",
        "filters_title": "Tiêu chí tìm kiếm",
        "filters_desc": "• Tỉnh thành / Khu công nghiệp\n• Thuê / Mua\n• Diện tích xây dựng / Đất\n• Điện, PCCC, chiều cao\n• Thời gian bàn giao",
        "filters_btn": "Gửi yêu cầu chi tiết",
        "listings_heading": "Thông tin tài sản công khai",
        "empty_title": "Hiện chưa có thông tin đạt tiêu chuẩn công bố",
        "empty_desc": "Chúng tôi không sử dụng tin giả hoặc hình ảnh minh họa không có thực. Quý khách có thể gửi yêu cầu trực tiếp để được tư vấn các nguồn phù hợp.",
        "contact_title": "Gửi yêu cầu & Đăng ký tài sản",
        "contact_desc": "Cung cấp thông tin chi tiết về nhu cầu đầu tư, thuê mua hoặc hợp tác xuyên biên giới tại Việt Nam.",
        "name_label": "Họ và tên",
        "company_label": "Công ty / Tổ chức",
        "contact_label": "Thông tin liên hệ",
        "contact_ph": "Email, số điện thoại hoặc Zalo/WeChat",
        "type_label": "Loại nhu cầu",
        "types": ["Tìm thuê nhà xưởng", "Tìm mua đất công nghiệp", "Tìm kho vận logistics", "Chuyển nhượng tài sản", "Hợp tác đầu tư", "Nhu cầu khác"],
        "target_city_label": "Tỉnh thành mục tiêu",
        "budget_label": "Ngân sách / Diện tích dự kiến",
        "message_label": "Chi tiết yêu cầu",
        "message_ph": "Mục đích sử dụng, mốc thời gian, tiêu chuẩn kỹ thuật đặc thù...",
        "agree_label": "Tôi hiểu rằng thông tin cần được xác minh chi tiết trước khi tiến hành giao dịch.",
        "submit_btn": "Gửi yêu cầu",
        "trust_title": "Nguyên tắc minh bạch & Tin cậy",
        "trust_desc": "Cam kết bảo lưu nguồn gốc, tiêu chuẩn kiểm duyệt nội dung và ranh giới sử dụng công nghệ AI.",
        "trust_cards": [
            ("Lưu giữ nguồn gốc", "Liên kết gốc, thời gian xuất bản, thời điểm thu thập và mã định danh luôn được đính kèm."),
            ("Kiểm duyệt tự động", "Hệ thống lọc tham số theo dõi, phát hiện trùng lặp và đánh giá rủi ro sơ bộ."),
            ("Tiêu chuẩn công bố", "Chỉ các thông tin đạt trạng thái kiểm duyệt mới hiển thị công khai; thông tin nháp hoặc ẩn sẽ không xuất hiện."),
            ("Đối chiếu trước giao dịch", "Giá cả, quyền sở hữu, giấy phép và điều kiện thực tế bắt buộc phải được xác minh cùng chủ đầu tư và chuyên gia."),
            ("Nguyên tắc minh bạch", "Không sử dụng tên khách hàng khi chưa có sự đồng ý hoặc tạo dựng các giao dịch giả mạo."),
            ("Giới hạn của AI", "AI chỉ hỗ trợ tổng hợp, phân loại và gợi ý tìm kiếm, không thay thế tư vấn pháp lý, tài chính hoặc khảo sát thực tế.")
        ],
        "opp_title": "Cơ hội hợp tác xuyên biên giới",
        "opp_desc": "Kết nối doanh nghiệp sản xuất, cung ứng và đầu tư giữa Trung Quốc, Việt Nam và các đối tác quốc tế.",
        "opp_cards": [
            ("Doanh nghiệp mở rộng sang Việt Nam", "Tư vấn nhà xưởng, khu công nghiệp, chuỗi cung ứng, thiết bị và nguồn lực đối tác địa phương."),
            ("Dự án Việt Nam kết nối nguồn lực quốc tế", "Kết nối thiết bị sản xuất, nguồn hàng, kênh phân phối, công nghệ và mô hình liên doanh."),
            ("Nguyên tắc công bố hợp tác", "Yêu cầu nêu rõ chủ thể, mục tiêu, nguồn lực, thời gian và thông tin liên hệ xác thực.")
        ],
        "cities_title": "Các tỉnh thành trọng điểm tại Việt Nam",
        "cities_desc": "Khám phá các trung tâm công nghiệp, hậu cần và kinh tế lớn nhất theo cụm và thế mạnh vùng.",
    },
    "zh": {
        "top_info": "Vietnam property intelligence · Sources retained · Verify before transaction",
        "brand_sub": "越南资产网 · Vietnam Assets",
        "nav": ("工业地产", "城市", "资产列表", "合作机会", "案例与信任", "提交询盘"),
        "footer_desc": "越南工业地产、商业资产与跨境合作的公开信息发现入口。保留来源，关键条件再次核验。",
        "assets_title": "资产",
        "services_title": "服务",
        "asset_links": [("厂房", "/zh/categories/factory/"), ("工业土地", "/zh/categories/industrial-land/"), ("仓库物流", "/zh/categories/warehouse/")],
        "service_links": [("搜索筛选", "/zh/listings/"), ("发布与询盘", "/zh/contact/"), ("核验原则", "/zh/trust/")],
        "disclaimer": "公开信息不构成交易、投资或法律建议。价格、产权、可用状态与合作条件须向原始发布方及专业顾问复核。",
        "search_ph": "搜索厂房、土地、仓库或合作需求",
        "city_ph": "全部重点城市",
        "search_btn": "搜索",
        "home_title": "越南资产，从发现到核验",
        "home_desc": "搜索越南厂房、工业土地、仓库、酒店与跨境合作机会。按城市与资产类型组织公开信息，保留来源并提供统一询盘入口。",
        "hero_kicker": "Industrial property · Commercial assets · Cooperation",
        "proof": [("6 类", "核心资产入口"), ("7 地", "重点产业城市"), ("100%", "来源与核验状态保留")],
        "sec1_title": "按资产类型进入",
        "sec1_desc": "围绕真实业务问题组织，不做杂乱信息堆积。",
        "sec2_title": "工业地产重点",
        "sec2_desc": "制造业选址、现成厂房、工业土地和仓储物流。",
        "sec3_title": "重点城市与产业走廊",
        "sec3_desc": "用城市专题承接区域比较、选址知识与最新公开信息。",
        "cta_home_title": "告诉我们你在越南要找什么",
        "cta_home_desc": "提交城市、面积、预算、用途和时间表。顾问团队将为您提供针对性匹配与实地核验指引。",
        "cta_home_btn": "提交需求",
        "market_title": "越南工业地产热门搜索",
        "market_text": "按城市和资产类型进入中文关键词专题，直接提交选址与资产需求。",
        "market_cta": "查看中文关键词导航",
        "home_seo_title": "越南工业地产网 | 厂房、土地与仓库选址",
        "home_seo_desc": "提供越南厂房、工业土地、仓库与跨境合作公开信息的发现与核验入口。",
        "breadcrumb_home": "首页",
        "read_more": "查看来源与详情 →",
        "faq_heading": "常见问题",
        "faq1_q": "信息是否已核验？",
        "faq1_a": "页面展示通过发布门槛的公开信息，并保留来源；价格、产权和即时可用性需进一步确认。",
        "faq2_q": "如何提交具体需求？",
        "faq2_a": "在询盘页填写城市、用途、面积、预算和时间表，系统将为您转入人工跟进与实地核验。",
        "filters_title": "筛选建议",
        "filters_desc": "城市 / 园区<br>租赁 / 购买<br>建筑面积 / 土地面积<br>电力 / 层高 / 消防<br>交付时间",
        "filters_btn": "提交结构化需求",
        "listings_heading": "公开资产与合作信息",
        "empty_title": "当前没有通过发布门槛的信息",
        "empty_desc": "我们不以演示房源冒充真实资产。可先提交需求，或稍后查看经来源核验的新条目。",
        "contact_title": "发布资产 / 提交询盘",
        "contact_desc": "结构化提交资产、选址或跨境合作需求。",
        "name_label": "您的姓名",
        "company_label": "公司 / 机构",
        "contact_label": "联系方式",
        "contact_ph": "邮箱、电话或微信",
        "type_label": "需求类型",
        "types": ["寻找厂房", "寻找工业土地", "寻找仓库", "出售/出租资产", "跨境合作", "其他"],
        "target_city_label": "目标城市",
        "budget_label": "预算 / 面积",
        "message_label": "需求详情",
        "message_ph": "用途、时间表、关键条件",
        "agree_label": "我理解平台信息需进一步核验",
        "submit_btn": "提交询盘",
        "trust_title": "案例与信任",
        "trust_desc": "了解信息来源、核验门槛、AI 使用边界与案例发布原则。",
        "trust_cards": [
            ("来源保留", "原始链接、发布时间、采集时间和内容指纹进入内容记录。"),
            ("自动清洗", "规则完成字段校验、追踪参数清理、重复检测和风险标记。"),
            ("发布门槛", "只有通过标准的信息才会进入公开列表；未通过或隐藏内容不会展示。"),
            ("交易前复核", "价格、产权、可用状态、许可与合同必须由项目方及专业顾问确认。"),
            ("案例说明", "当前不展示未经授权的客户名称或虚构成交案例。后续仅发布可验证、获授权的案例。"),
            ("AI 使用边界", "AI 仅用于整理、分类和匹配建议，不替代法律、财务或现场尽调。")
        ],
        "opp_title": "跨境合作机会",
        "opp_desc": "连接中国企业与越南本地资产、供应链及合作资源。",
        "opp_cards": [
            ("中国企业进入越南", "厂房、园区、仓储、设备、供应链与本地合作资源。"),
            ("越南项目对接中国资源", "设备、货源、渠道、技术、采购及联合经营。"),
            ("合作发布原则", "说明主体、目标、资源、时间表和可验证联系方式。")
        ],
        "cities_title": "越南重点城市",
        "cities_desc": "按产业集群、物流条件和资产类型进入区域专题。",
    },
    "en": {
        "top_info": "Vietnam property intelligence · Sources retained · Verify before transaction",
        "brand_sub": "VietnamZiChan · Vietnam Assets",
        "nav": ("Industrial", "Cities", "Listings", "Opportunities", "Trust", "Enquire"),
        "footer_desc": "Public information portal for industrial real estate, commercial assets and cross-border cooperation in Vietnam. Sources retained and verified.",
        "assets_title": "Assets",
        "services_title": "Services",
        "asset_links": [("Factories", "/en/categories/factory/"), ("Industrial Land", "/en/categories/industrial-land/"), ("Warehouses", "/en/categories/warehouse/")],
        "service_links": [("Listings", "/en/listings/"), ("Enquiry", "/en/contact/"), ("Trust Principles", "/en/trust/")],
        "disclaimer": "Public information does not constitute investment, financial or legal advice. Prices, titles, availability and cooperation terms must be verified with primary sources and professional advisors.",
        "search_ph": "Search factories, land, warehouses or cooperation",
        "city_ph": "All key cities",
        "search_btn": "Search",
        "home_title": "Vietnam Assets, from Discovery to Verification",
        "home_desc": "Explore factories, industrial land, warehouses, hotels and cross-border opportunities in Vietnam. Source-led discovery with a clear verification path.",
        "hero_kicker": "Industrial property · Commercial assets · Cooperation",
        "proof": [("6 Categories", "Core asset portals"), ("7 Cities", "Key industrial hubs"), ("100%", "Sources & status retained")],
        "sec1_title": "Explore by Asset Type",
        "sec1_desc": "Structured around real business requirements without clutter.",
        "sec2_title": "Industrial Real Estate Focus",
        "sec2_desc": "Manufacturing sites, ready-built factories, industrial land and warehousing logistics.",
        "sec3_title": "Key Cities & Economic Corridors",
        "sec3_desc": "Regional hubs providing area comparison, selection knowledge and latest public updates.",
        "cta_home_title": "Tell Us What You Are Looking For in Vietnam",
        "cta_home_desc": "Submit city, area, budget, purpose and timeline. Our team will assist with structured matching and verification.",
        "cta_home_btn": "Submit Requirement",
        "market_title": "Popular Industrial Real Estate Searches",
        "market_text": "Browse keyword hubs by city and asset type to submit targeted property requirements.",
        "market_cta": "View Regional Keyword Hub",
        "home_seo_title": "Vietnam Industrial Property Portal | Factories & Land",
        "home_seo_desc": "Discover verified public listings and cross-border investment opportunities across key Vietnamese industrial cities.",
        "breadcrumb_home": "Home",
        "read_more": "View Source & Details →",
        "faq_heading": "Frequently Asked Questions",
        "faq1_q": "Are property listings verified?",
        "faq1_a": "Pages display public listings that meet our publication threshold with retained sources. Pricing, titles and real-time availability require secondary confirmation.",
        "faq2_q": "How do I submit a specific requirement?",
        "faq2_a": "Complete our enquiry form with location, purpose, area, budget and timeline. Our advisors will coordinate verification and follow-up.",
        "filters_title": "Search Filters",
        "filters_desc": "• City / Industrial Park\n• Lease / Purchase\n• Built / Land Area\n• Power / Ceiling / Fire safety\n• Delivery timeline",
        "filters_btn": "Submit Structured Requirement",
        "listings_heading": "Public Assets & Cooperation Listings",
        "empty_title": "No listings currently meet the publication threshold",
        "empty_desc": "We do not use placeholder listings. You can submit your requirement or check back for newly verified entries.",
        "contact_title": "Enquire & Submit Asset",
        "contact_desc": "Submit your industrial property, site selection or cross-border cooperation requirements.",
        "name_label": "Your Name",
        "company_label": "Company / Organization",
        "contact_label": "Contact Information",
        "contact_ph": "Email, phone or WeChat/Zalo",
        "type_label": "Requirement Type",
        "types": ["Looking for Factory", "Looking for Industrial Land", "Looking for Warehouse", "Sell / Lease Asset", "Cross-border Cooperation", "Other"],
        "target_city_label": "Target City",
        "budget_label": "Budget / Area",
        "message_label": "Requirement Details",
        "message_ph": "Purpose, timeline, key technical specs",
        "agree_label": "I understand platform information requires further verification.",
        "submit_btn": "Submit Enquiry",
        "trust_title": "Trust & Transparency",
        "trust_desc": "Learn about information provenance, publication thresholds, AI boundaries and publishing principles.",
        "trust_cards": [
            ("Source Retention", "Original links, publication timestamps, collection dates and content fingerprints are preserved."),
            ("Automated Curation", "Rules handle field validation, tracking parameter cleanup, duplicate detection and risk flags."),
            ("Publication Threshold", "Only approved listings enter the public directory; unverified or hidden items are not shown."),
            ("Pre-Transaction Review", "Pricing, legal titles, availability, licenses and contracts must be confirmed by project owners and advisors."),
            ("Publishing Principles", "We do not display unauthorized client names or fictitious transactions. Only verifiable cases are published."),
            ("AI Boundaries", "AI is used strictly for organization, classification and matching suggestions, not as legal, financial or survey advice.")
        ],
        "opp_title": "Cross-Border Cooperation Opportunities",
        "opp_desc": "Connecting Chinese enterprises with local Vietnamese assets, supply chains and cooperative resources.",
        "opp_cards": [
            ("Chinese Enterprises Entering Vietnam", "Factories, parks, warehousing, equipment, supply chain and local partner resources."),
            ("Vietnam Projects Meeting Chinese Resources", "Equipment, sourcing, distribution channels, technology, procurement and joint operations."),
            ("Cooperation Publishing Principles", "Clearly state entities, objectives, resources, timelines and verifiable contact details.")
        ],
        "cities_title": "Key Cities in Vietnam",
        "cities_desc": "Explore top industrial, logistics and commercial hubs by cluster and regional advantage.",
    }
}

def shell(title: str, description: str, body: str, path: str, lang: str = "zh", schema: dict | None = None) -> str:
    locale, _ = LANGS[lang]
    canonical = f"{SITE}{path}"
    graph = schema or {"@context":"https://schema.org","@type":"WebPage","name":title,"url":canonical,"description":description,"inLanguage":locale}
    ui = UI[lang]
    nav = ui["nav"]
    zh_label = "ZH" if lang == "vi" else "中文"
    return f'''<!doctype html><html lang="{locale}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} | VietnamZiChan</title><meta name="description" content="{html.escape(description, quote=True)}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{canonical}"><link rel="alternate" hreflang="zh-CN" href="{SITE}/zh/"><link rel="alternate" hreflang="vi-VN" href="{SITE}/vi/"><link rel="alternate" hreflang="en" href="{SITE}/en/"><meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(description, quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:type" content="website"><meta name="twitter:card" content="summary"><link rel="stylesheet" href="/assets/site.css"><script type="application/ld+json">{json.dumps(graph,ensure_ascii=False).replace('</','<\\/')}</script></head><body><div class="top"><div class="wrap"><span>{ui["top_info"]}</span><span class="lang"><a href="/zh/">中文</a><a href="/vi/">Tiếng Việt</a><a href="/en/">English</a></span></div></div><div class="nav-shell"><nav class="wrap nav"><a class="brand" href="/{lang}/">VietnamZiChan<small>{ui["brand_sub"]}</small></a><div class="links"><a href="/{lang}/categories/factory/">{nav[0]}</a><a href="/{lang}/cities/">{nav[1]}</a><a href="/{lang}/listings/">{nav[2]}</a><a href="/{lang}/opportunities/">{nav[3]}</a><a href="/{lang}/trust/">{nav[4]}</a></div><a class="action" href="/{lang}/contact/">{nav[5]}</a></nav></div>{body}<footer class="footer"><div class="wrap footer-grid"><div><h3>VietnamZiChan</h3><p>{ui["footer_desc"]}</p></div><div><h3>{ui["assets_title"]}</h3>{''.join(f'<a href="{url}">{name}</a>' for name, url in ui["asset_links"])}</div><div><h3>{ui["services_title"]}</h3>{''.join(f'<a href="{url}">{name}</a>' for name, url in ui["service_links"])}</div></div><div class="wrap fine">{ui["disclaimer"]}</div></footer><script src="/assets/site.js?v=2" defer></script></body></html>'''

def cards(items, base, lang="zh"):
    idx = {"vi": 2, "zh": 0, "en": 1}[lang]
    view_text = {"vi": "Xem chi tiết →", "zh": "查看专题 →", "v": "View →", "en": "View →"}[lang if lang in ("vi", "zh") else "en"]
    return '<div class="grid">' + ''.join(f'<a class="card" href="/{lang}/{base}/{slug}/"><span class="eyebrow">Vietnam market</span><h3>{html.escape(v[idx][0])}</h3><p>{html.escape(v[idx][3])}</p><span class="arrow">{view_text}</span></a>' for slug, v in items.items()) + '</div>'

def home(lang="zh"):
    ui = UI[lang]
    c_list = list(CITIES.values())
    idx = {"vi": 2, "zh": 0, "en": 1}[lang]
    city_options = ''.join(f'<option value="{c[idx][0]}">{c[idx][0]}</option>' for c in c_list)
    body = f'''<header class="hero"><div class="wrap hero-grid"><div><span class="kicker">{ui["hero_kicker"]}</span><h1>{ui["home_title"]}</h1><p>{ui["home_desc"]}</p><form class="search" data-search><input name="q" aria-label="Keyword" placeholder="{ui["search_ph"]}"><select name="city" aria-label="City"><option value="">{ui["city_ph"]}</option>{city_options}</select><button class="btn">{ui["search_btn"]}</button></form></div><aside class="proof"><div><b>{ui["proof"][0][0]}</b>{ui["proof"][0][1]}</div><div><b>{ui["proof"][1][0]}</b>{ui["proof"][1][1]}</div><div><b>{ui["proof"][2][0]}</b>{ui["proof"][2][1]}</div></div></aside></div></header><main><section class="section"><div class="wrap"><div class="head"><div><h2>{ui["sec1_title"]}</h2><p>{ui["sec1_desc"]}</p></div><a class="arrow" href="/{lang}/listings/">{ui["nav"][2]} →</a></div>{cards(CATEGORIES, 'categories', lang)}</div></section><section class="section industrial"><div class="wrap"><div class="head"><div><h2>{ui["sec2_title"]}</h2><p>{ui["sec2_desc"]}</p></div></div>{cards(dict(list(CATEGORIES.items())[:3]), 'categories', lang)}</div></section><section class="section"><div class="wrap"><div class="head"><div><h2>{ui["sec3_title"]}</h2><p>{ui["sec3_desc"]}</p></div></div>{cards(CITIES, 'cities', lang)}</div></section><section class="section"><div class="wrap"><div class="cta"><div><h2>{ui["cta_home_title"]}</h2><p>{ui["cta_home_desc"]}</p></div><a class="btn" href="/{lang}/contact/">{ui["cta_home_btn"]}</a></div></div></section></main>'''
    if lang in ("vi", "zh"):
        body = body.replace('</main>', f'<section class="section"><div class="wrap"><div class="cta"><div><h2>{ui["market_title"]}</h2><p>{ui["market_text"]}</p></div><a class="btn" href="/{lang}/market/">{ui["market_cta"]}</a></div></div></section></main>')
    schema = {"@context": "https://schema.org", "@graph": [{"@type": "Organization", "name": "VietnamZiChan", "url": SITE}, {"@type": "WebSite", "name": "VietnamZiChan", "url": f"{SITE}/{lang}/", "potentialAction": {"@type": "SearchAction", "target": f"{SITE}/{lang}/listings/?q={{search_term_string}}", "query-input": "required name=search_term_string"}}]}
    return shell(ui["home_seo_title"], ui["home_seo_desc"], body, f"/{lang}/", lang, schema)

def landing(kind, slug, data, lang="zh"):
    ui = UI[lang]
    idx = {"vi": 2, "zh": 0, "en": 1}[lang]
    entry = data[idx]
    name = entry[0]
    desc = entry[3]
    noun = ("Danh mục" if lang=="vi" else ("资产类型" if lang=="zh" else "Category")) if kind == "categories" else ("Tỉnh thành" if lang=="vi" else ("重点城市" if lang=="zh" else "City"))
    home_lbl = ui["breadcrumb_home"]
    faq = f'''<section class="section faq"><div class="wrap"><div class="head"><div><h2>{ui["faq_heading"]}</h2></div></div><details><summary>{ui["faq1_q"]}</summary><p>{ui["faq1_a"]}</p></details><details><summary>{ui["faq2_q"]}</summary><p>{ui["faq2_a"]}</p></details></div></section>'''
    body = f'''<main><div class="page-hero"><div class="wrap"><div class="breadcrumb"><a href="/{lang}/">{home_lbl}</a> / {noun}</div><span class="kicker">Vietnam market guide</span><h1>{name}</h1><p>{desc}. Chuyên trang tổng hợp thông tin, tiêu chí kỹ thuật và quy trình kết nối.</p><div class="facts"><div class="fact"><b>1. Xác định nhu cầu</b><br><span>Mục đích, diện tích, ngân sách</span></div><div class="fact"><b>2. Kiểm tra nguồn</b><br><span>Trạng thái, pháp lý, giới hạn</span></div><div class="fact"><b>3. Kết nối chuyên gia</b><br><span>Khảo sát và tư vấn trực tiếp</span></div></div></div></div><section class="section"><div class="wrap listing-layout"><aside class="filters"><span class="eyebrow">{name}</span><h3>{ui["filters_title"]}</h3><p style="white-space:pre-line">{ui["filters_desc"]}</p><a class="btn" href="/{lang}/contact/">{ui["filters_btn"]}</a></aside><div><div class="head"><div><h2>{name} - {ui["listings_heading"]}</h2><p data-count>Đang tải dữ liệu...</p></div></div><div class="grid" data-list><div class="empty full"><h3>{ui["empty_title"]}</h3><p>{ui["empty_desc"]}</p><a class="arrow" href="/{lang}/contact/">{ui["cta_home_btn"]} →</a></div></div></div></div></section>{faq}</main>'''
    schema = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": name, "description": desc, "url": f"{SITE}/{lang}/{kind}/{slug}/"}, {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": ui["faq1_q"], "acceptedAnswer": {"@type": "Answer", "text": ui["faq1_a"]}}]}]}
    return shell(name, desc, body, f"/{lang}/{kind}/{slug}/", lang, schema)

def simple_page(name, path, content, lang="zh"):
    ui = UI[lang]
    home_lbl = ui["breadcrumb_home"]
    body = f'<main><div class="page-hero"><div class="wrap"><div class="breadcrumb"><a href="/{lang}/">{home_lbl}</a> / {name}</div><h1>{name}</h1><p>{content}</p></div></div><section class="section"><div class="wrap">'
    if path == "listings":
        idx = {"vi": 2, "zh": 0, "en": 1}[lang]
        city_opts = ''.join(f'<option>{c[idx][0]}</option>' for c in CITIES.values())
        keyword_label = {"vi": "Từ khóa", "zh": "关键词", "en": "Keyword"}[lang]
        city_label = {"vi": "Tỉnh thành", "zh": "城市", "en": "City"}[lang]
        loading_label = {"vi": "Đang tải...", "zh": "正在加载...", "en": "Loading..."}[lang]
        body += f'''<div class="listing-layout"><aside class="filters"><form data-search><label>{keyword_label}</label><input name="q" placeholder="{ui["search_ph"]}"><label>{city_label}</label><select name="city"><option value="">{ui["city_ph"]}</option>{city_opts}</select><p><button class="btn" style="margin-top:12px">{ui["search_btn"]}</button></p></form></aside><div><div class="head"><div><h2>{ui["listings_heading"]}</h2><p data-count>{loading_label}</p></div></div><div class="grid" data-list><div class="empty full"><h3>{ui["empty_title"]}</h3><p>{ui["empty_desc"]}</p></div></div></div></div>'''
    elif path == "contact":
        types_opts = ''.join(f'<option>{t}</option>' for t in ui["types"])
        body += f'''<form class="form" name="inquiry" method="POST" data-netlify="true" netlify-honeypot="bot-field"><input type="hidden" name="form-name" value="inquiry"><p hidden><label>Don't fill <input name="bot-field"></label></p><div class="form-grid"><label>{ui["name_label"]}<input name="name" required></label><label>{ui["company_label"]}<input name="company"></label><label>{ui["contact_label"]}<input name="contact" required placeholder="{ui["contact_ph"]}"></label><label>{ui["type_label"]}<select name="type">{types_opts}</select></label><label>{ui["target_city_label"]}<input name="city"></label><label>{ui["budget_label"]}<input name="budget_area"></label><label class="full">{ui["message_label"]}<textarea name="message" required placeholder="{ui["message_ph"]}"></textarea></label><label class="full"><input style="width:auto" type="checkbox" required> {ui["agree_label"]}</label><div class="full"><button class="btn" type="submit">{ui["submit_btn"]}</button></div></div></form>'''
    elif path == "trust":
        cards_html = ''.join(f'<div class="card step"><h3>{c[0]}</h3><p>{c[1]}</p></div>' for c in ui["trust_cards"])
        body += f'<div class="grid">{cards_html}</div>'
    else:
        cards_html = ''.join(f'<div class="card"><h3>{c[0]}</h3><p>{c[1]}</p></div>' for c in ui["opp_cards"])
        body += f'<div class="grid">{cards_html}</div><div class="notice" style="margin-top:20px">{ui["disclaimer"]}</div>'
    body += '</div></section></main>'
    return shell(name, content, body, f"/{lang}/{path}/", lang)

def seo_market_landing(lang, city_slug, city, type_slug, asset):
    ui = UI[lang]
    idx = {"vi": 2, "zh": 0, "en": 1}[lang]
    city_entry = city[idx]
    asset_entry = asset[idx]
    city_name = city_entry[0]
    asset_name = asset_entry[0]
    details = asset_entry[3]
    if lang == "zh":
        title = f"{city_name}{asset_name}｜越南工业地产与选址需求对接"
        description = f"寻找{city_name}{asset_name}：{details}。提交面积、预算、用途、电力、消防和交付时间，进入越南资产需求匹配。"
        kicker, lead = "越南工业地产关键词专题", f"面向正在寻找{city_name}{asset_name}的企业和投资者，集中整理区域判断、技术条件、核验步骤与询盘入口。"
        labels = ("为什么关注这个区域", "采购方需要准备", "如何开始", "产业与物流条件", "用途、面积与预算", "提交需求并安排核验", "提交需求")
    elif lang == "vi":
        title = f"{asset_name} tại {city_name} | Bất động sản công nghiệp"
        description = f"Tìm {asset_name.lower()} tại {city_name}: {details}. Gửi diện tích, ngân sách, mục đích, điện, PCCC và thời gian bàn giao."
        kicker, lead = "Chuyên trang bất động sản công nghiệp Việt Nam", f"Dành cho doanh nghiệp đang tìm {asset_name.lower()} tại {city_name}, với tiêu chí kỹ thuật, quy trình xác minh và kênh gửi yêu cầu rõ ràng."
        labels = ("Vì sao nên xem khu vực này", "Thông tin cần chuẩn bị", "Bước tiếp theo", "Cụm công nghiệp và logistics", "Mục đích, diện tích và ngân sách", "Gửi yêu cầu để sắp xếp xác minh", "Gửi yêu cầu")
    else:
        title = f"{asset_name} in {city_name} | Vietnam Industrial Property"
        description = f"Looking for {asset_name.lower()} in {city_name}: {details}. Submit area, budget, purpose, power, fire safety and delivery timeline."
        kicker, lead = "Vietnam Industrial Property Hub", f"For enterprises seeking {asset_name.lower()} in {city_name}, with technical criteria and verification guidance."
        labels = ("Why this location", "Preparation", "Next steps", "Industrial & logistics cluster", "Purpose, area & budget", "Submit requirement for verification", "Submit enquiry")

    path = f"/{lang}/market/{city_slug}/{type_slug}/"
    criteria = {"vi": "• Vị trí<br>• Diện tích<br>• Công suất điện<br>• PCCC<br>• Ngân sách", "zh": "• 位置<br>• 面积<br>• 电力<br>• 消防<br>• 预算", "en": "• Location<br>• Area<br>• Power<br>• Fire safety<br>• Budget"}[lang]
    technical = {"vi": "Công suất điện, tải trọng sàn, chiều cao, PCCC và yêu cầu môi trường.", "zh": "电力、地面承重、层高、消防及环保条件。", "en": "Power, floor load, ceiling height, fire safety and environmental compliance."}[lang]
    body = f'''<main><div class="page-hero"><div class="wrap"><div class="breadcrumb"><a href="/{lang}/">{ui["breadcrumb_home"]}</a> / {city_name} / {asset_name}</div><span class="kicker">{kicker}</span><h1>{title}</h1><p>{lead}</p><div class="facts"><div class="fact"><b>{labels[0]}</b><br><span>{labels[3]}</span></div><div class="fact"><b>{labels[1]}</b><br><span>{labels[4]}</span></div><div class="fact"><b>{labels[2]}</b><br><span>{labels[5]}</span></div></div></div></div><section class="section"><div class="wrap listing-layout"><aside class="filters"><span class="eyebrow">{city_name} · {asset_name}</span><h3>{labels[1]}</h3><p>{details}</p><p>{criteria}</p><a class="btn" href="/{lang}/contact/">{labels[6]}</a></aside><div><div class="head"><div><h2>{city_name} - {asset_name}</h2><p>{description}</p></div></div><div class="grid"><div class="card"><span class="eyebrow">Location</span><h3>{labels[3]}</h3><p>{details}</p></div><div class="card"><span class="eyebrow">Technical</span><h3>{labels[4]}</h3><p>{technical}</p></div><div class="card"><span class="eyebrow">Verification</span><h3>{labels[5]}</h3><p>{ui["faq1_a"]}</p></div></div><div class="cta" style="margin-top:22px"><div><h2>{title}</h2><p>{description}</p></div><a class="btn" href="/{lang}/contact/">{labels[6]}</a></div></div></div></section></main>'''
    schema = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": title, "description": description, "url": f"{SITE}{path}", "inLanguage": LANGS[lang][0]}]}
    return shell(title, description, body, path, lang, schema)

def seo_hub(lang):
    ui = UI[lang]
    title = "越南厂房、工业土地与仓库城市导航" if lang == "zh" else ("Nhà xưởng, đất công nghiệp và kho theo tỉnh thành" if lang == "vi" else "Industrial Property & Warehouse Hub by City")
    desc = "按北宁、平阳、同奈、海防、河内、胡志明市和岘港查找越南工业地产。" if lang == "zh" else ("Tìm nhà xưởng, đất công nghiệp và kho tại các tỉnh thành trọng điểm Việt Nam." if lang == "vi" else "Explore industrial properties across key Vietnamese cities and economic zones.")
    links = []
    idx = {"vi": 2, "zh": 0, "en": 1}[lang]
    for city_slug, city in CITIES.items():
        city_name = city[idx][0]
        for type_slug, asset in SEO_TYPES.items():
            asset_name = asset[idx][0]
            links.append(f'<a class="card" href="/{lang}/market/{city_slug}/{type_slug}/"><span class="eyebrow">{city_name}</span><h3>{city_name} · {asset_name}</h3><p>{asset[idx][3]}</p><span class="arrow">Xem chi tiết →</span></a>')
    body = f'<main><div class="page-hero"><div class="wrap"><div class="breadcrumb"><a href="/{lang}/">{ui["breadcrumb_home"]}</a> / Hub</div><span class="kicker">SEO Keyword Hub</span><h1>{title}</h1><p>{desc}</p></div></div><section class="section"><div class="wrap"><div class="grid">{"".join(links)}</div></div></section></main>'
    return shell(title, desc, body, f"/{lang}/market/", lang)

def write(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text + "\n", encoding="utf-8")

def build():
    write("assets/site.css", CSS)
    write("assets/site.js", JS)
    write(".portal-built.json", json.dumps({"schema_version": "1.0", "runtime": "static-local"}, ensure_ascii=False))
    write("index.html", '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/vi/"><link rel="canonical" href="https://vietnamzichan.com/vi/"><title>VietnamZiChan</title></head><body><a href="/vi/">Vào VietnamZiChan</a></body></html>')
    for lang in LANGS:
        write(f"{lang}/index.html", home(lang))
        write(f"{lang}/cities/index.html", shell("Các tỉnh thành trọng điểm", "Danh mục tỉnh thành công nghiệp Việt Nam", f'<main><div class="page-hero"><div class="wrap"><div class="breadcrumb"><a href="/{lang}/">{UI[lang]["breadcrumb_home"]}</a> / Cities</div><h1>{UI[lang]["cities_title"]}</h1><p>{UI[lang]["cities_desc"]}</p></div></div><section class="section"><div class="wrap">{cards(CITIES, "cities", lang)}</div></section></main>', f"/{lang}/cities/", lang))
        for kind, dataset in (("categories", CATEGORIES), ("cities", CITIES)):
            for slug, data in dataset.items():
                write(f"{lang}/{kind}/{slug}/index.html", landing(kind, slug, data, lang))
        for slug, name, desc in (("listings", "资产搜索与筛选" if lang=="zh" else ("Danh sách tài sản" if lang=="vi" else "Listings"), "搜索已通过发布门槛的越南资产与合作信息。" if lang=="zh" else ("Tìm kiếm và lọc thông tin tài sản và hợp tác tại Việt Nam." if lang=="vi" else "Search and filter verified property listings.")),
                                 ("contact", "发布资产 / 提交询盘" if lang=="zh" else ("Liên hệ & Gửi yêu cầu" if lang=="vi" else "Enquiry"), "结构化提交资产、选址或跨境合作需求。" if lang=="zh" else ("Gửi yêu cầu cấu trúc về bất động sản hoặc hợp tác." if lang=="vi" else "Submit structured requirements.")),
                                 ("trust", "案例与信任" if lang=="zh" else ("Tin cậy & Minh bạch" if lang=="vi" else "Trust & Principles"), "了解信息来源、核验门槛、AI 使用边界与案例发布原则。" if lang=="zh" else ("Tìm hiểu về nguồn gốc, quy chuẩn kiểm duyệt và nguyên tắc minh bạch." if lang=="vi" else "Learn about provenance and verification.")),
                                 ("opportunities", "跨境合作机会" if lang=="zh" else ("Cơ hội hợp tác" if lang=="vi" else "Opportunities"), "连接中国企业与越南本地资产、供应链及合作资源。" if lang=="zh" else ("Kết nối doanh nghiệp và nguồn lực hợp tác tại Việt Nam." if lang=="vi" else "Cross-border cooperation."))):
            write(f"{lang}/{slug}/index.html", simple_page(name, slug, desc, lang))
        if lang in ("vi", "zh", "en"):
            write(f"{lang}/market/index.html", seo_hub(lang))
            for city_slug, city in CITIES.items():
                for type_slug, asset in SEO_TYPES.items():
                    write(f"{lang}/market/{city_slug}/{type_slug}/index.html", seo_market_landing(lang, city_slug, city, type_slug, asset))
    return sum(1 for _ in ROOT.rglob("*.html"))

if __name__ == "__main__":
    build()
    print(json.dumps({"status": "ok", "portal": "rebuilt"}, ensure_ascii=False))
