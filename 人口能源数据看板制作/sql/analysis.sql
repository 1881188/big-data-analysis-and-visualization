-- The dashboard creates these three tables from the accepted CSVs in memory.
-- All years and energy keys supplied by the application use bound parameters.
SELECT p.year,p.population_total,p.urbanization_pct,e.energy_total,e.living_energy_per_capita
FROM population p JOIN energy e ON p.year=e.year
WHERE p.year BETWEEN :first AND :last ORDER BY p.year;

-- Selected category retains its complete history.
SELECT year,energy_name,share_pct,amount_estimated_tce_10k,share_change_pp
FROM structure WHERE year BETWEEN :first AND :last AND energy_key=:energy ORDER BY year;

-- Base-year arithmetic decomposition (add the rounding residual change separately).
SELECT now.energy_key,now.energy_name,
       now.amount_estimated_tce_10k-base.amount_estimated_tce_10k AS delta_tce_10k
FROM structure now JOIN structure base ON now.energy_key=base.energy_key
WHERE now.year=:year AND base.year=:base ORDER BY now.energy_key;
