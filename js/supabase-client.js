// Public config — the anon/publishable key is designed to be exposed client-side.
// Real access control lives in Postgres Row Level Security policies, not in secrecy of this key.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

export const supabase = createClient(
  'https://rpfccljejzfixohgwtpr.supabase.co',
  'sb_publishable_t5inMT0ym3KrCQqkRLOK4w_HAhS7q3S'
);
