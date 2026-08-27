-- 五站共享社区底座：一个 Supabase 项目、一张 posts 表、多站复用。
-- 幂等：可以在任意一个已经跑过 002_posts.sql（或完全没跑过）的项目状态上重复执行。
-- 运行方式：Supabase 控制台 -> SQL Editor -> New query -> 粘贴 -> Run。整个项目只需要跑一次
-- （不管你在哪个站的 supabase/ 目录里看到这份文件，它们是同一份、指向同一个项目）。

-- 1) 基线表：如果 002_posts.sql 从未跑过，这里补建一个最小结构，后面再统一加字段。
create table if not exists public.posts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users on delete cascade not null,
  display_name text not null,
  kind text not null,
  target text,
  title text,
  body text not null,
  created_at timestamptz not null default now()
);

-- 2) 补齐多站共用字段（对已存在的表安全追加，不影响旧数据）。
alter table public.posts add column if not exists site text not null default 'soulentropy';
alter table public.posts add column if not exists category text;
alter table public.posts add column if not exists tags text[] not null default '{}';
alter table public.posts add column if not exists status text not null default 'active';
alter table public.posts add column if not exists cross_post_sites text[] not null default '{}';
alter table public.posts add column if not exists updated_at timestamptz;

-- 3) 约束：站点白名单 + 状态白名单 + 放宽后的 kind 词表（新增通用 'post'，保留旧值兼容历史数据）。
alter table public.posts drop constraint if exists posts_site_check;
alter table public.posts add constraint posts_site_check
  check (site in ('soulentropy','vietnamzichan','vietchiphub','vngo','brdiag','globalewaste'));

alter table public.posts drop constraint if exists posts_status_check;
alter table public.posts add constraint posts_status_check
  check (status in ('active','hidden'));

alter table public.posts drop constraint if exists posts_kind_check;
alter table public.posts add constraint posts_kind_check
  check (kind in ('post','comment','board','resource_offer','resource_need','resource_trade','case'));

-- 4) 索引：按站点+类型+时间是最常见查询，tags 用 GIN 支持数组包含查询。
create index if not exists posts_site_kind_created_idx on public.posts (site, kind, created_at desc);
create index if not exists posts_site_category_idx on public.posts (site, category);
create index if not exists posts_target_idx on public.posts (target);
create index if not exists posts_tags_gin_idx on public.posts using gin (tags);
create index if not exists posts_status_idx on public.posts (status);

-- 5) RLS：公开只读"未被隐藏"的内容；作者永远能看到/改/删自己的内容（不管状态）。
alter table public.posts enable row level security;

drop policy if exists "Posts are viewable by everyone" on public.posts;
drop policy if exists "Active posts are viewable by everyone, owners see their own" on public.posts;
create policy "Active posts are viewable by everyone, owners see their own"
  on public.posts for select
  using (status = 'active' or auth.uid() = user_id);

drop policy if exists "Authenticated users can create their own posts" on public.posts;
create policy "Authenticated users can create their own posts"
  on public.posts for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users can update their own posts" on public.posts;
create policy "Users can update their own posts"
  on public.posts for update
  using (auth.uid() = user_id);

drop policy if exists "Users can delete their own posts" on public.posts;
create policy "Users can delete their own posts"
  on public.posts for delete
  using (auth.uid() = user_id);

-- 6) 举报表：最小审核能力——真正的"管理后台"就是 Supabase 控制台的 Table Editor，
--    管理员直接在里面把某条 posts.status 改成 'hidden' 即可下架，不需要额外开发一套后台系统。
--    这张表只是让用户可以提交举报，方便管理员在控制台里筛选待处理项。
create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  post_id uuid references public.posts on delete cascade not null,
  reporter_user_id uuid references auth.users on delete cascade not null,
  reason text not null default 'user_reported',
  created_at timestamptz not null default now()
);
create index if not exists reports_post_idx on public.reports (post_id);

alter table public.reports enable row level security;

drop policy if exists "Authenticated users can file a report" on public.reports;
create policy "Authenticated users can file a report"
  on public.reports for insert
  with check (auth.uid() = reporter_user_id);
-- 有意不加 select 策略：普通用户看不到举报列表，管理员通过控制台（服务角色）查看，绕过 RLS。

-- 7) 最小防灌水：同一个用户 10 分钟内最多发 8 条，超过直接在数据库层拒绝。
--    这是"最小限制"而不是复杂风控系统——先卡住最基本的脚本刷帖，够用为止。
create or replace function public.posts_rate_limit()
returns trigger as $$
declare
  recent_count int;
begin
  select count(*) into recent_count
  from public.posts
  where user_id = new.user_id
    and created_at > now() - interval '10 minutes';
  if recent_count >= 8 then
    raise exception 'RATE_LIMITED: 发布太频繁，请稍后再试';
  end if;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists posts_rate_limit_trigger on public.posts;
create trigger posts_rate_limit_trigger
  before insert on public.posts
  for each row execute function public.posts_rate_limit();
