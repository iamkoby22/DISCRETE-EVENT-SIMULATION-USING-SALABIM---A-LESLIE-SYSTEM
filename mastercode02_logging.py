# mastercode02_logging.py
import pandas as pd
import numpy as np
import mastercode02_globals as g
import traceback
from mastercode02_config_and_rates import (SIMULATION_DURATION, ROAD_NETWORK_CAPACITY,
                                             BANK_SAVINGS_ANNUAL_CAPACITY, BANK_LOAN_ANNUAL_CAPACITY,
                                             GOVERNMENT_SPENDING_ANNUAL_CAP)

LOG_DATA = {
    'population_datasheet': [], 'household_datasheet': [], 'annual_summary': [],
    'marriage_summary': [], 'vehicle_events': [], 'trip_summary': [], 'rates_summary': [],
    'resource_summary': [],
    'scores_summary': []
}

def log_yearly_data(year, env, growth_rate):
    if year == SIMULATION_DURATION:
        _log_population_datasheet(year)
        _log_household_datasheet(year)

    _log_annual_summary(year, env, growth_rate)
    _log_new_summaries(year, env)
    _log_annual_resource_summary(year, env)
    _log_annual_scores(year, env)

def _log_population_datasheet(year):
    for p in g.POPULATION:
        household = g.HOUSEHOLDS.get(p.household_id, {})
        marriage_info = next((m for m in reversed(LOG_DATA['marriage_summary']) if m.get('man_id') == p.id or m.get('woman_id') == p.id), None)
        LOG_DATA['population_datasheet'].append({
            'year': year, 'person_id': p.id, 'age': p.age, 'sex': p.sex,
            'new household_id': p.household_id, 'household_type': household.get('type', 'N/A'),
            'Household Id Before marriage': marriage_info.get('man_former_hh') if marriage_info and p.id == marriage_info.get('man_id') else (marriage_info.get('woman_former_hh') if marriage_info else 'N/A'),
            'marital_status': p.marital_status,
            'Spouses former Household Id': marriage_info.get('woman_former_hh') if marriage_info and p.id == marriage_info.get('man_id') else (marriage_info.get('man_former_hh') if marriage_info else 'N/A'),
            'education_level': p.education, 'employment_status': p.employment_status,
            'Emplolyment Rank': p.skill_level, 'employer': p.employer,
            'Layoff/ dismissed / quit before?': p.layoff_status,
            'Has a car?': bool(p.cars), 'Car ID': ", ".join([str(c['id']) for c in p.cars]), 'Use the Bus?': p.use_bus,
            'Accident Involvement': p.accident_involvement,
            'Most used Purpose of comutation': p.commute_purpose,
            'Annual Income': p.annual_income, 'Gov_support_cum per person': p.gov_support_cum
        })

def _log_household_datasheet(year):
    for hh_id, hh_data in g.HOUSEHOLDS.items():
        members = hh_data.get('members', [])
        if not members: continue
        LOG_DATA['household_datasheet'].append({
            'household_id': hh_id, 'household_type': hh_data.get('type'), 'household_members': len(members),
            'births_in_hh': hh_data.get('births', 0), 'deaths_in_hh': hh_data.get('deaths', 0), 'marriages_in_hh': hh_data.get('marriages', 0),
            'students_in_hh': sum(1 for p in members if 'University' in p.education or 'program' in p.education),
            'employed_in_hh': sum(1 for p in members if p.employment_status == 'Employed'),
            'Have a car?': any(p.cars for p in members), 'How many cars in household': sum(len(p.cars) for p in members),
            'use bus?': any(p.use_bus for p in members),
            'Household Annual Income': hh_data.get('total_income', 0), 'Required Cost_Pre tax': hh_data.get('required_cost', 0),
            'Net_income_minus_cost': hh_data.get('total_income', 0) - hh_data.get('required_cost', 0),
            'Savings Balance': hh_data.get('savings_balance', 0), 'Loan Balance': hh_data.get('loan_balance', 0),
            'Loan Repaid_cum': hh_data.get('loan_repaid_cum', 0), 'Gov_support_cum': sum(p.gov_support_cum for p in members), 'Taxes_cum': hh_data.get('taxes_cum', 0)
        })

def _log_annual_summary(year, env, growth_rate):
    current_pop = len(g.POPULATION)
    prev_pop = current_pop / (1 + growth_rate) if (1 + growth_rate) != 0 else current_pop
    births = sum(h.get('births', 0) for h in g.HOUSEHOLDS.values()); deaths = sum(h.get('deaths', 0) for h in g.HOUSEHOLDS.values())
    employed = sum(1 for p in g.POPULATION if p.employment_status == 'Employed'); labor_force = sum(1 for p in g.POPULATION if p.employment_status not in ['Too Young', 'Retired', 'student'])
    all_incomes = [p.annual_income for p in g.POPULATION if p.annual_income > 0]; all_costs = [h.get('required_cost', 0) for h in g.HOUSEHOLDS.values()]
    all_savings = [h.get('savings_balance', 0) for h in g.HOUSEHOLDS.values()]; all_loans = [h.get('loan_balance', 0) for h in g.HOUSEHOLDS.values()]
    LOG_DATA['annual_summary'].append({
        'Year': year, 'Population': current_pop, 'Households': len(g.HOUSEHOLDS), 'Population Growth rate': growth_rate,
        'No of births': births, 'Birth rate': births / prev_pop if prev_pop > 0 else 0,
        'No. of Deaths': deaths, 'Death rate': deaths / prev_pop if prev_pop > 0 else 0,
        'Employment Rate': employed / labor_force if labor_force > 0 else 0,
        'Avg Annual Income': np.mean(all_incomes or [0]), 'Avg Annual Req Cost': np.mean(all_costs or [0]),
        'Avg Savings Balance': np.mean(all_savings or [0]), 'Avg Loan Balance': np.mean(all_loans or [0]),
        'Total Number of Cars': sum(len(p.cars) for p in g.POPULATION),
        'Number of Accidents on road': g.ANNUAL_SUMMARY_DATA.get('num_accidents', 0),
        'Cost Inflation rate': env.cpi_inflation,
    })
    for hh in g.HOUSEHOLDS.values(): hh['births'] = 0; hh['deaths'] = 0; hh['marriages'] = 0

def _log_new_summaries(year, env):
    LOG_DATA['marriage_summary'].extend(g.MARRIAGES); g.MARRIAGES.clear()
    LOG_DATA['vehicle_events'].extend(g.VEHICLE_EVENTS); g.VEHICLE_EVENTS.clear()
    if g.TRIP_SUMMARY:
        df = pd.DataFrame(g.TRIP_SUMMARY); purpose_counts = df.groupby('purpose').size().reset_index(name='count'); purpose_counts['year'] = year
        LOG_DATA['trip_summary'].append(purpose_counts)
    g.TRIP_SUMMARY.clear()
    LOG_DATA['rates_summary'].append({ 'year': year, 'arima_death_rate_mod': g.arima_death_rate_modifier, 'event_death_rate_mod': g.event_death_rate_modifier, 'tax_rate': env.tax_rate, 'salary_inflation': env.salary_inflation, 'cpi_inflation': env.cpi_inflation })

def _log_annual_resource_summary(year, env):
    for level_name, res in g.EDUCATION_RESOURCE.items():
        stats = g.annual_education_stats.get(level_name, {'in_use': 0, 'refused': 0}); capacity = res.capacity(); in_use = stats['in_use']; refused = stats['refused']
        LOG_DATA['resource_summary'].append({ 'year': year, 'name': level_name, 'capacity': capacity, 'in_use': in_use, 'waiting_or_refused': refused, 'utilization': in_use / capacity if capacity > 0 else 0 })
    for res in g.EMPLOYER_RESOURCE.values():
        capacity = res.capacity(); in_use = res.claimed_quantity(); waiting = len(res.requesters())
        LOG_DATA['resource_summary'].append({ 'year': year, 'name': res.name(), 'capacity': capacity, 'in_use': in_use, 'waiting_or_refused': waiting, 'utilization': in_use / capacity if capacity > 0 else 0 })
    LOG_DATA['resource_summary'].append({'year': year, 'name': 'Bank (Savings)', 'capacity': BANK_SAVINGS_ANNUAL_CAPACITY, 'in_use': g.annual_savings_accepted, 'waiting_or_refused': g.refused_log['savings'], 'utilization': g.annual_savings_accepted / BANK_SAVINGS_ANNUAL_CAPACITY if BANK_SAVINGS_ANNUAL_CAPACITY > 0 else 0})
    LOG_DATA['resource_summary'].append({'year': year, 'name': 'Bank (Loan)', 'capacity': BANK_LOAN_ANNUAL_CAPACITY, 'in_use': g.annual_loans_disbursed, 'waiting_or_refused': g.refused_log['loans'], 'utilization': g.annual_loans_disbursed / BANK_LOAN_ANNUAL_CAPACITY if BANK_LOAN_ANNUAL_CAPACITY > 0 else 0})
    LOG_DATA['resource_summary'].append({'year': year, 'name': 'Government Support', 'capacity': GOVERNMENT_SPENDING_ANNUAL_CAP, 'in_use': g.annual_gov_support_disbursed, 'waiting_or_refused': g.refused_log['gov_support'], 'utilization': g.annual_gov_support_disbursed / GOVERNMENT_SPENDING_ANNUAL_CAP if GOVERNMENT_SPENDING_ANNUAL_CAP > 0 else 0})
    bus_capacity = getattr(env, 'total_bus_capacity', 0); bus_served = getattr(env, 'bus_passengers_served', 0); bus_refused = getattr(env, 'bus_passengers_refused', 0)
    LOG_DATA['resource_summary'].append({'year': year, 'name': 'Bus Service', 'capacity': bus_capacity, 'in_use': bus_served, 'waiting_or_refused': bus_refused, 'utilization': bus_served / bus_capacity if bus_capacity > 0 else 0})
    total_cars = sum(len(p.cars) for p in g.POPULATION)
    for road_type, capacity in ROAD_NETWORK_CAPACITY.items():
        LOG_DATA['resource_summary'].append({'year': year, 'name': f'Road: {road_type}', 'capacity': capacity, 'in_use': total_cars, 'waiting_or_refused': 0, 'utilization': total_cars / capacity if capacity > 0 else 0})
    g.annual_savings_accepted = 0; g.annual_loans_disbursed = 0; g.annual_gov_support_disbursed = 0
    g.refused_log = {'savings': 0, 'loans': 0, 'gov_support': 0}; g.annual_education_stats.clear()

def _log_annual_scores(year, env):
    def normalize(value, min_val, max_val, lower_is_better=False):
        if lower_is_better: value, min_val, max_val = -value, -max_val, -min_val
        if (max_val - min_val) == 0: return 0.5
        return max(0, min(1, (value - min_val) / (max_val - min_val)))
    summary = LOG_DATA['annual_summary'][-1]; households = list(g.HOUSEHOLDS.values())
    net_incomes = [h.get('total_income', 0) - h.get('taxes_cum', 0) - h.get('required_cost', 0) for h in households]
    savings = [h.get('savings_balance', 0) for h in households]; loans = [h.get('loan_balance', 0) for h in households]
    norm_inflation = normalize(summary['Cost Inflation rate'], 0.0, 0.15, lower_is_better=True)
    norm_gov_spend = normalize(g.annual_gov_support_disbursed, 0, GOVERNMENT_SPENDING_ANNUAL_CAP * (g.event_gov_cap_modifier or 1))
    norm_employment = normalize(summary['Employment Rate'], 0.85, 1.0)
    norm_net_income = normalize(np.median(net_incomes) if net_incomes else 0, -50000, 20000)
    norm_savings = normalize(np.median(savings) if savings else 0, 0, 50000)
    norm_loans = normalize(np.median(loans) if loans else 0, 0, 200000, lower_is_better=True)
    eco_index = (norm_inflation * 0.2 + norm_gov_spend * 0.1 + norm_employment * 0.3 + norm_net_income * 0.2 + norm_savings * 0.1 + norm_loans * 0.1) * 100
    total_cars = summary['Total Number of Cars']; high_risk_drivers = len([p for p in g.POPULATION if 16 <= p.age <= 21 and p.cars])
    old_vehicles = sum(1 for p in g.POPULATION for car in p.cars if car.get('age',0) >= 8)
    road_util = total_cars / sum(ROAD_NETWORK_CAPACITY.values()) if sum(ROAD_NETWORK_CAPACITY.values()) > 0 else 0
    norm_congestion = normalize(road_util, 0.2, 1.0, lower_is_better=True)
    norm_accidents = normalize(summary['Number of Accidents on road'], 50, 500, lower_is_better=True)
    norm_old_cars = normalize(old_vehicles / total_cars if total_cars > 0 else 0, 0.1, 0.75, lower_is_better=True)
    norm_risk_drivers = normalize(high_risk_drivers / total_cars if total_cars > 0 else 0, 0.05, 0.4, lower_is_better=True)
    trans_index = (norm_congestion * 0.4 + norm_accidents * 0.3 + norm_old_cars * 0.15 + norm_risk_drivers * 0.15) * 100
    LOG_DATA['scores_summary'].append({'year': year, 'economic_index': eco_index, 'transport_index': trans_index})
    g.latest_economic_index = eco_index

def write_and_close_csv_logs(base_filename, env):
    print(f"\n--- Writing final logs to CSV files with base name: {base_filename} ---")
    try:
        float_format = '%.2f'
        if LOG_DATA['population_datasheet']: pd.DataFrame(LOG_DATA['population_datasheet']).to_csv(f"{base_filename}_population_datasheet.csv", index=False, float_format=float_format)
        if LOG_DATA['household_datasheet']: pd.DataFrame(LOG_DATA['household_datasheet']).to_csv(f"{base_filename}_household_datasheet.csv", index=False, float_format=float_format)
        pd.DataFrame(LOG_DATA['annual_summary']).to_csv(f"{base_filename}_annual_summary.csv", index=False, float_format=float_format)
        if LOG_DATA['marriage_summary']: pd.DataFrame(LOG_DATA['marriage_summary']).to_csv(f"{base_filename}_summary_marriages.csv", index=False)
        if LOG_DATA['vehicle_events']: pd.DataFrame(LOG_DATA['vehicle_events']).to_csv(f"{base_filename}_summary_vehicle_events.csv", index=False)
        if LOG_DATA['trip_summary']: pd.concat(LOG_DATA['trip_summary']).to_csv(f"{base_filename}_summary_trips.csv", index=False)
        if LOG_DATA['rates_summary']: pd.DataFrame(LOG_DATA['rates_summary']).to_csv(f"{base_filename}_summary_rates.csv", index=False, float_format=float_format)
        if LOG_DATA['resource_summary']: pd.DataFrame(LOG_DATA['resource_summary']).to_csv(f"{base_filename}_summary_resources.csv", index=False, float_format=float_format)
        if LOG_DATA['scores_summary']: pd.DataFrame(LOG_DATA['scores_summary']).to_csv(f"{base_filename}_scores_summary.csv", index=False, float_format=float_format)
        print("...All CSV log files saved successfully. ✅")
    except Exception:
        print("\n--- A CRITICAL ERROR OCCURRED DURING CSV FILE WRITING ---"); traceback.print_exc()