REBUILD_RANK_NORMS_SQL = """
INSERT INTO app.rank_norms (real_rank_tier, real_rank_division, p10, p95, k_rank, updated_at)
SELECT
  u.real_rank_tier,
  u.real_rank_division,
  percentile_disc(0.10) WITHIN GROUP (ORDER BY pl.total)::double precision AS p10,
  percentile_disc(0.95) WITHIN GROUP (ORDER BY pl.total)::double precision AS p95,
  -- choose your rank constants here (example values; tweak later)
  CASE u.real_rank_tier
    WHEN 'IRON' THEN 0.85
    WHEN 'BRONZE' THEN 0.90
    WHEN 'SILVER' THEN 0.95
    WHEN 'GOLD' THEN 1.00
    WHEN 'PLATINUM' THEN 1.05
    WHEN 'EMERALD' THEN 1.08
    WHEN 'DIAMOND' THEN 1.10
    WHEN 'MASTER' THEN 1.15
    WHEN 'GRANDMASTER' THEN 1.20
    WHEN 'CHALLENGER' THEN 1.25
    ELSE 1.00
  END AS k_rank,
  now()
FROM app.power_levels pl
JOIN app.users u ON u.puuid = pl.puuid
WHERE u.real_rank_tier IS NOT NULL
GROUP BY u.real_rank_tier, u.real_rank_division
ON CONFLICT (real_rank_tier, COALESCE(real_rank_division, ''))
DO UPDATE SET
  p10 = EXCLUDED.p10,
  p95 = EXCLUDED.p95,
  k_rank = EXCLUDED.k_rank,
  updated_at = EXCLUDED.updated_at;
"""