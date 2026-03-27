-- ============================================================
-- Cleanup: Fix companies with URL-like names in the database
-- Run this AFTER deploying the name_sanitizer.py code changes.
-- ============================================================

-- 1. PREVIEW: See which companies have URL-like names
SELECT id, company_name, company_name_normalized, total_postings_alltime
FROM companies
WHERE company_name LIKE 'http://%'
   OR company_name LIKE 'https://%'
   OR company_name LIKE 'www.%'
ORDER BY total_postings_alltime DESC;

-- 2. FIX: Update company names by extracting from LinkedIn URLs
-- Pattern: https://in.linkedin.com/jobs/view/{title}-at-{company}-{id}
UPDATE companies
SET company_name = initcap(
    replace(
        (regexp_match(company_name, '-at-([a-z0-9-]+)-\d+$'))[1],
        '-', ' '
    )
),
company_name_normalized = lower(
    replace(
        (regexp_match(company_name, '-at-([a-z0-9-]+)-\d+$'))[1],
        '-', ' '
    )
)
WHERE company_name LIKE '%linkedin.com/jobs/view/%'
  AND (regexp_match(company_name, '-at-([a-z0-9-]+)-\d+$'))[1] IS NOT NULL;

-- 3. FIX: Update company names from career site domains
-- Pattern: https://meesho.io/jobs/... → Meesho
UPDATE companies
SET company_name = initcap(
    split_part(
        split_part(
            replace(replace(company_name, 'https://', ''), 'http://', ''),
            '/', 1
        ),
        '.', 1
    )
),
company_name_normalized = lower(
    split_part(
        split_part(
            replace(replace(company_name, 'https://', ''), 'http://', ''),
            '/', 1
        ),
        '.', 1
    )
)
WHERE (company_name LIKE 'https://%' OR company_name LIKE 'http://%')
  AND company_name NOT LIKE '%linkedin.com%'
  AND company_name NOT LIKE '%bayt.com%'
  AND company_name NOT LIKE '%naukrigulf.com%'
  AND company_name NOT LIKE '%indeed.com%'
  AND company_name NOT LIKE '%glassdoor.com%';

-- 4. VERIFY: Check if any URL names remain
SELECT id, company_name
FROM companies
WHERE company_name LIKE 'http://%'
   OR company_name LIKE 'https://%'
   OR company_name LIKE 'www.%';

-- 5. MERGE DUPLICATES: After name fixes, some companies may now have
--    the same normalized name as existing ones. Check for these:
SELECT company_name_normalized, count(*), array_agg(id)
FROM companies
WHERE company_name_normalized IS NOT NULL
GROUP BY company_name_normalized
HAVING count(*) > 1;
