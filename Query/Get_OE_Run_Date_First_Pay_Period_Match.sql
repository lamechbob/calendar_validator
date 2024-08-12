-- Query searches for Clients whom have an OE Run Date that is greater than ANY Run Date on their calendar

select d.company_id,TRIM(UPPER(REGEXP_REPLACE(comp.name,'[^a-zA-Z ]',''))) AS "NAME",d.oe_payroll_file_date, s.pay_group_id, s.pr_cycle_number, s.cutoff_date
from company_plan_detail d, payroll_schedule s, company_payroll_config_detail g, company comp
where d.plan_year = '2024'
and d.plan_year = g.plan_year
and s.pay_group_id = g.pay_group_id
and d.company_id = g.company_id
and comp.company_id = g.company_id
and payroll_oe_rundate is null
and d.plan_year = s.pr_schedule_year
and d.oe_payroll_file_date >= s.cutoff_date
AND COMP.COMPANY_ID NOT IN('31652','31667','31687','31688','31725')
AND UPPER(COMP.NAME) NOT LIKE '%TEST%';