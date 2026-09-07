-- VietnamZiChan Listing Desk v1
-- Structured, AI-assisted, staff-reviewed listing submissions.
-- Reuses the shared Supabase auth/community project (site='vietnamzichan').
--
-- STATUS: already applied directly via the Supabase SQL Editor on the live
-- project (rpfccljejzfixohgwtpr) on 2026-09-07. This file is kept here for
-- documentation/reproducibility (the live `supabase/` migrations folder used
-- by other local tooling is gitignored in this repo). All statements are
-- idempotent (if not exists / or replace / drop-then-create policy), so
-- re-running this file is safe.

create table if not exists public.listing_submissions (
  id uuid primary key default gen_random_uuid(),
  site text not null default 'vietnamzichan',
  submitted_by uuid not null references auth.users(id),
  submitter_role text not null default 'user' check (submitter_role in ('user','staff')),
  listing_type text not null check (listing_type in ('sell','rent','buy','lease','cooperation')),
  raw_text text not null,
  city_region text,
  category text,
  price_text text,
  area_text text,
  contact_text text,
  images jsonb not null default '[]'::jsonb,
  ai jsonb,
  status text not null default 'RAW' check (status in ('RAW','AI_PROCESSED','PENDING_REVIEW','APPROVED','PUBLISHED','NEEDS_INFO','REJECTED')),
  reviewer_id uuid references auth.users(id),
  reviewer_note text,
  published_slug text,
  published_url text,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists listing_submissions_status_idx on public.listing_submissions (site, status);
create index if not exists listing_submissions_owner_idx on public.listing_submissions (submitted_by);

create table if not exists public.site_staff (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id),
  site text not null,
  role text not null default 'staff',
  created_at timestamptz not null default now(),
  unique (user_id, site)
);

create or replace function public.is_site_staff(p_site text)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.site_staff where user_id = auth.uid() and site = p_site)
$$;

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists listing_submissions_set_updated_at on public.listing_submissions;
create trigger listing_submissions_set_updated_at
  before update on public.listing_submissions
  for each row execute function public.set_updated_at();

alter table public.listing_submissions enable row level security;
alter table public.site_staff enable row level security;

drop policy if exists "owner can insert own submissions" on public.listing_submissions;
create policy "owner can insert own submissions" on public.listing_submissions
for insert to authenticated
with check (submitted_by = auth.uid());

drop policy if exists "owner or staff can view" on public.listing_submissions;
create policy "owner or staff can view" on public.listing_submissions
for select to authenticated
using (submitted_by = auth.uid() or public.is_site_staff(site) or status = 'PUBLISHED');

drop policy if exists "owner can update own while editable" on public.listing_submissions;
create policy "owner can update own while editable" on public.listing_submissions
for update to authenticated
using (submitted_by = auth.uid() and status in ('RAW','NEEDS_INFO'))
with check (submitted_by = auth.uid());

drop policy if exists "staff can update any" on public.listing_submissions;
create policy "staff can update any" on public.listing_submissions
for update to authenticated
using (public.is_site_staff(site))
with check (public.is_site_staff(site));

drop policy if exists "owner can delete own raw" on public.listing_submissions;
create policy "owner can delete own raw" on public.listing_submissions
for delete to authenticated
using (submitted_by = auth.uid() and status = 'RAW');

drop policy if exists "staff can delete any" on public.listing_submissions;
create policy "staff can delete any" on public.listing_submissions
for delete to authenticated
using (public.is_site_staff(site));

drop policy if exists "self can view own staff row" on public.site_staff;
create policy "self can view own staff row" on public.site_staff
for select to authenticated
using (user_id = auth.uid());

insert into storage.buckets (id, name, public)
values ('listing-images','listing-images', true)
on conflict (id) do nothing;

drop policy if exists "public can read listing images" on storage.objects;
create policy "public can read listing images" on storage.objects
for select using (bucket_id = 'listing-images');

drop policy if exists "authenticated can upload own listing images" on storage.objects;
create policy "authenticated can upload own listing images" on storage.objects
for insert to authenticated
with check (bucket_id = 'listing-images' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "owner can delete own listing images" on storage.objects;
create policy "owner can delete own listing images" on storage.objects
for delete to authenticated
using (bucket_id = 'listing-images' and (storage.foldername(name))[1] = auth.uid()::text);
