// 五站共享社区组件库 · community-core.js
// 部署到每个站点时，只需要改下面这一行 SITE 常量，其余逻辑全部通用。
// 依赖同一个 Supabase 项目里统一结构的 posts 表（见 supabase/003_shared_community.sql）：
// site / kind / category / target / title / body / tags / status / cross_post_sites。
import { supabase } from '/js/supabase-client.js';

const SITE = 'vietnamzichan'; // <- 每个站点的 vendored 副本改这一行，比如 'soulentropy' / 'vietnamzichan'

export function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

export function formatTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  } catch { return iso; }
}

export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession();
  return session;
}

// 渲染顶部导航里的"账号/加入社区"状态。传入一个容器元素 id。
export async function renderAuthState(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return null;
  const session = await getSession();
  if (session && session.user) {
    const name = (session.user.user_metadata && session.user.user_metadata.display_name) || session.user.email;
    el.innerHTML = `已登录：${escapeHtml(name)} · <a href="#" id="communityLogoutLink">退出</a>`;
    const logoutLink = document.getElementById('communityLogoutLink');
    if (logoutLink) {
      logoutLink.addEventListener('click', async (e) => {
        e.preventDefault();
        await supabase.auth.signOut();
        window.location.reload();
      });
    }
  } else {
    el.innerHTML = '<a href="/signup/" class="cta-join">加入社区</a> · <a href="/login/">登录</a>';
  }
  return session;
}

// 发一条帖子/回复。kind: post | comment | board | resource_offer | resource_need | resource_trade | case
// category：该站自己的业务分类（比如 VietChipHub 用 'BUY'/'SELL'/'RFQ'，SoulEntropy 用 '讨论'/'案例'）。
// target：挂载点，比如给某条帖子回复时传 `post:<id>`，给某个固定页面挂评论时传 'home' 之类的字符串。
export async function submitPost({ kind, category = null, target = null, title = null, body, tags = [] }) {
  const session = await getSession();
  if (!session || !session.user) {
    throw new Error('NEED_LOGIN');
  }
  const displayName = (session.user.user_metadata && session.user.user_metadata.display_name) || session.user.email;
  const { data, error } = await supabase
    .from('posts')
    .insert({
      user_id: session.user.id,
      display_name: displayName,
      site: SITE,
      kind,
      category,
      target,
      title,
      body,
      tags: (tags && tags.length) ? tags : [],
    })
    .select()
    .single();
  if (error) {
    if (String(error.message || '').includes('RATE_LIMITED')) throw new Error('发布太频繁，请稍后再试');
    throw error;
  }
  return data;
}

export async function fetchPosts({ kind, category = null, target = null, tag = null, q = null, limit = 50 }) {
  let query = supabase.from('posts').select('*').eq('site', SITE).eq('kind', kind).eq('status', 'active').order('created_at', { ascending: false }).limit(limit);
  if (target !== null) query = query.eq('target', target);
  if (category !== null) query = query.eq('category', category);
  if (tag !== null) query = query.contains('tags', [tag]);
  if (q) query = query.or(`title.ilike.%${q}%,body.ilike.%${q}%`);
  const { data, error } = await query;
  if (error) throw error;
  return data || [];
}

export async function updatePost(id, body) {
  const { error } = await supabase.from('posts').update({ body, updated_at: new Date().toISOString() }).eq('id', id);
  if (error) throw error;
}

export async function deletePost(id) {
  const { error } = await supabase.from('posts').delete().eq('id', id);
  if (error) throw error;
}

export async function reportPost(id, reason = 'user_reported') {
  const session = await getSession();
  if (!session || !session.user) throw new Error('NEED_LOGIN');
  const { error } = await supabase.from('reports').insert({ post_id: id, reporter_user_id: session.user.id, reason });
  if (error) throw error;
}

// 渲染一个通用留言/评论/帖子列表到指定容器。自带"编辑/删除"（本人）和"举报"（他人）按钮。
export function renderPostList(containerId, posts, { emptyText = '还没有内容，来写第一条吧。', showTitle = false, actionable = true } = {}) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!posts.length) {
    el.innerHTML = `<p class="empty">${escapeHtml(emptyText)}</p>`;
    return;
  }
  const render = (uid) => {
    el.innerHTML = posts.map((p) => {
      const mine = actionable && uid && p.user_id === uid;
      const tagsHtml = (p.tags && p.tags.length) ? `<div class="post-tags">${p.tags.map((t) => `<span class="tag-pill">${escapeHtml(t)}</span>`).join('')}</div>` : '';
      const actions = !actionable ? '' : (mine
        ? `<button type="button" class="post-action" data-act="edit" data-id="${p.id}">编辑</button><button type="button" class="post-action" data-act="delete" data-id="${p.id}">删除</button>`
        : `<button type="button" class="post-action" data-act="report" data-id="${p.id}">举报</button>`);
      return `<article class="post-item" data-post-id="${p.id}">
        ${showTitle && p.title ? `<h3>${escapeHtml(p.title)}</h3>` : ''}
        <p class="post-body" data-body>${escapeHtml(p.body)}</p>
        ${tagsHtml}
        <div class="post-meta">${escapeHtml(p.display_name)} · ${formatTime(p.created_at)}${p.updated_at ? ' · 已编辑' : ''} <span class="post-actions">${actions}</span></div>
      </article>`;
    }).join('');
    if (!actionable) return;
    el.querySelectorAll('.post-action').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        const act = btn.dataset.act;
        const article = el.querySelector(`[data-post-id="${id}"]`);
        if (act === 'delete') {
          if (!confirm('确定删除这条内容？删除后无法恢复。')) return;
          try { await deletePost(id); article.remove(); } catch (e) { alert('删除失败：' + (e && e.message ? e.message : e)); }
        } else if (act === 'edit') {
          const bodyEl = article.querySelector('[data-body]');
          const current = (posts.find((p) => String(p.id) === String(id)) || {}).body || '';
          const next = prompt('修改内容：', current);
          if (next === null || !next.trim()) return;
          try { await updatePost(id, next.trim()); bodyEl.textContent = next.trim(); } catch (e) { alert('修改失败：' + (e && e.message ? e.message : e)); }
        } else if (act === 'report') {
          if (!confirm('确定要举报这条内容给管理员吗？')) return;
          try { await reportPost(id); btn.textContent = '已举报'; btn.disabled = true; } catch (e) {
            if (e && e.message === 'NEED_LOGIN') alert('请先登录后再举报。');
            else alert('举报失败：' + (e && e.message ? e.message : e));
          }
        }
      });
    });
  };
  getSession().then((session) => render(session && session.user ? session.user.id : null));
}

// 挂一个"发帖表单"的提交事件。formId 表单里必须有 id=postBody 的 textarea，
// 可选 id=postTitle 的 input，可选 id=postTags 的 input（逗号分隔）。
export function wirePostForm({ formId, msgId, kind, category = null, target = null, onSuccess }) {
  const form = document.getElementById(formId);
  if (!form) return;
  const msg = document.getElementById(msgId);
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (msg) { msg.textContent = ''; msg.className = 'msg'; }
    const bodyEl = form.querySelector('#postBody');
    const titleEl = form.querySelector('#postTitle');
    const tagsEl = form.querySelector('#postTags');
    const catEl = form.querySelector('#postCategory');
    const body = bodyEl ? bodyEl.value.trim() : '';
    const title = titleEl ? titleEl.value.trim() : null;
    const tags = tagsEl ? tagsEl.value.split(',').map((t) => t.trim()).filter(Boolean) : [];
    const cat = catEl ? catEl.value : category;
    if (!body) return;
    const btn = form.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      await submitPost({ kind, category: cat, target, title: title || null, body, tags });
      if (bodyEl) bodyEl.value = '';
      if (titleEl) titleEl.value = '';
      if (tagsEl) tagsEl.value = '';
      if (msg) { msg.textContent = '已发布。'; msg.className = 'msg ok'; }
      if (onSuccess) await onSuccess();
    } catch (err) {
      if (err && err.message === 'NEED_LOGIN') {
        if (msg) { msg.textContent = '请先登录或注册后再发布。'; msg.className = 'msg err'; }
      } else {
        if (msg) { msg.textContent = '发布失败：' + (err && err.message ? err.message : String(err)); msg.className = 'msg err'; }
      }
    } finally {
      if (btn) btn.disabled = false;
    }
  });
}
