// Listing Desk v1 · 结构化房源/需求提交与员工审核队列
// 复用 /js/supabase-client.js 里同一个 Supabase 项目（登录/注册/community.js 共用）。
// 表结构见仓库根目录 supabase/010_listing_desk_v1.sql。
import { supabase } from '/js/supabase-client.js';
import { getSession } from '/js/community.js';

const SITE = 'vietnamzichan';
const BUCKET = 'listing-images';

export const LISTING_TYPES = ['sell', 'rent', 'buy', 'lease', 'cooperation'];
export const CATEGORIES = ['factory', 'industrial-land', 'warehouse', 'hotel', 'residential', 'agriculture'];
export const CITIES = ['ho-chi-minh-city', 'binh-duong', 'dong-nai', 'hanoi', 'bac-ninh', 'hai-phong', 'da-nang'];

export function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

// 是否是本站（vietnamzichan）员工。依赖 010_listing_desk_v1.sql 里的 is_site_staff() 函数，
// 该函数用 security definer 只读 site_staff 表，普通用户看不到别人是不是员工。
export async function isStaff() {
  const session = await getSession();
  if (!session || !session.user) return false;
  const { data, error } = await supabase.rpc('is_site_staff', { p_site: SITE });
  if (error) return false;
  return !!data;
}

// 上传图片到 listing-images bucket，路径按 uid 分文件夹（RLS 要求）。返回公开 URL 数组。
export async function uploadListingImages(files) {
  const session = await getSession();
  if (!session || !session.user) throw new Error('NEED_LOGIN');
  const uid = session.user.id;
  const urls = [];
  for (const file of files) {
    if (!file || !file.type || !file.type.startsWith('image/')) continue;
    if (file.size > 8 * 1024 * 1024) throw new Error('图片过大（单张限 8MB）：' + file.name);
    const ext = (file.name.split('.').pop() || 'jpg').toLowerCase().replace(/[^a-z0-9]/g, '') || 'jpg';
    const path = `${uid}/${Date.now()}-${Math.random().toString(36).slice(2, 8)}.${ext}`;
    const { error } = await supabase.storage.from(BUCKET).upload(path, file, { upsert: false });
    if (error) throw error;
    const { data } = supabase.storage.from(BUCKET).getPublicUrl(path);
    if (data && data.publicUrl) urls.push(data.publicUrl);
  }
  return urls;
}

// 提交一条新的房源/需求草稿（status=RAW，等私有 Ollama worker 处理）。
export async function submitListing({ listingType, rawText, cityRegion = null, category = null, priceText = null, areaText = null, contactText = null, images = [] }) {
  const session = await getSession();
  if (!session || !session.user) throw new Error('NEED_LOGIN');
  if (!LISTING_TYPES.includes(listingType)) throw new Error('listingType 无效');
  if (!rawText || !rawText.trim()) throw new Error('内容不能为空');
  const staff = await isStaff();
  const { data, error } = await supabase
    .from('listing_submissions')
    .insert({
      site: SITE,
      submitted_by: session.user.id,
      submitter_role: staff ? 'staff' : 'user',
      listing_type: listingType,
      raw_text: rawText.trim(),
      city_region: cityRegion || null,
      category: category || null,
      price_text: priceText || null,
      area_text: areaText || null,
      contact_text: contactText || null,
      images,
    })
    .select()
    .single();
  if (error) throw error;
  return data;
}

// 当前用户自己提交过的记录（提交表单下方的"我的提交"状态列表）。
export async function fetchMySubmissions(limit = 20) {
  const session = await getSession();
  if (!session || !session.user) return [];
  const { data, error } = await supabase
    .from('listing_submissions')
    .select('id, listing_type, raw_text, status, reviewer_note, published_url, created_at, updated_at')
    .eq('submitted_by', session.user.id)
    .order('created_at', { ascending: false })
    .limit(limit);
  if (error) throw error;
  return data || [];
}

// —— 以下仅员工可用（受 RLS "owner or staff can view" / "staff can update any" 保护，
//     非员工调用会因为查不到行 / 更新不了行而实质上无效，不依赖前端隐藏来做安全边界）——

export async function fetchQueue(status = 'PENDING_REVIEW', limit = 50) {
  const { data, error } = await supabase
    .from('listing_submissions')
    .select('*')
    .eq('site', SITE)
    .eq('status', status)
    .order('created_at', { ascending: true })
    .limit(limit);
  if (error) throw error;
  return data || [];
}

async function reviewUpdate(id, patch) {
  const session = await getSession();
  if (!session || !session.user) throw new Error('NEED_LOGIN');
  const { error } = await supabase
    .from('listing_submissions')
    .update({ ...patch, reviewer_id: session.user.id })
    .eq('id', id);
  if (error) throw error;
}

export async function approveSubmission(id, note = null) {
  return reviewUpdate(id, { status: 'APPROVED', reviewer_note: note });
}

export async function rejectSubmission(id, note) {
  if (!note || !note.trim()) throw new Error('拒绝需要填写原因');
  return reviewUpdate(id, { status: 'REJECTED', reviewer_note: note.trim() });
}

export async function requestInfo(id, note) {
  if (!note || !note.trim()) throw new Error('请说明缺什么信息');
  return reviewUpdate(id, { status: 'NEEDS_INFO', reviewer_note: note.trim() });
}

export const STATUS_LABELS_ZH = {
  RAW: '待AI处理', AI_PROCESSED: 'AI已处理', PENDING_REVIEW: '待审核',
  APPROVED: '已批准·待发布', PUBLISHED: '已发布', NEEDS_INFO: '需要补充信息', REJECTED: '已拒绝',
};
