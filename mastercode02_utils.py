# mastercode02_utils.py
from mastercode02_config_and_rates import COST_GRID

def classify_household_for_cost(members):
    """Determines a household's composition for cost calculation."""
    adults = sum(1 for p in members if p.age >= 18)
    children = sum(1 for p in members if p.age < 18)
    working_adults = sum(1 for p in members if p.age >= 18 and p.employment_status == 'Employed')

    if adults <= 1:
        adults_key = "1_adult"
    else: # 2 or more adults
        adults_key = "2_adults_2_working" if working_adults >= 2 else "2_adults_1_working"

    return adults, children, working_adults, adults_key

def compute_household_cost(members, cpi_inflation_multiplier):
    """Calculates the detailed annual cost for a household based on its composition."""
    if not members:
        return 0

    adults, children, working_adults, adults_key = classify_household_for_cost(members)

    # Base cost for the adults and up to 3 children
    child_idx = min(children, 3)
    total_cost = sum(COST_GRID[category][adults_key][child_idx] for category in COST_GRID)

    # Add cost for extra children if any
    if children > 3:
        # Calculate the marginal cost of one extra child
        cost_3_children = sum(COST_GRID[category][adults_key][3] for category in COST_GRID)
        cost_2_children = sum(COST_GRID[category][adults_key][2] for category in COST_GRID)
        marginal_child_cost = cost_3_children - cost_2_children
        total_cost += (children - 3) * marginal_child_cost

    # Add cost for extra adults if any
    if adults > 2:
        cost_2_adults = sum(COST_GRID[category]["2_adults_2_working"][0] for category in COST_GRID)
        cost_1_adult = sum(COST_GRID[category]["1_adult"][0] for category in COST_GRID)
        marginal_adult_cost = cost_2_adults - cost_1_adult
        total_cost += (adults - 2) * marginal_adult_cost

    # Apply the global CPI inflation multiplier
    return total_cost * cpi_inflation_multiplier