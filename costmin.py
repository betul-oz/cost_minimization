from pulp import LpMinimize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD

# Demand of dental implantation (number)
demand = {
    "A1": 7, "A2": 18, "A3": 14, "A4": 11, "A5": 3, 
    "B1": 3, "B2": 6, "B3": 17, "B4": 12, 
    "C1": 14, "C2": 4, "C3": 15, "C4": 19, 
    "D2": 16, "D3": 5, "D4": 2
}

# Ceramic powder costs ($/kg) by suppliers
costs = {
    "supplier 1": {"white": 35, "yellow": 32, "pink": 45, "gray": 50},
    "supplier 2": {"white": 32, "yellow": 20, "pink": 30, "gray": 40},
    "supplier 3": {"white": 24, "yellow": 18, "pink": 20, "gray": 35}
}

# Amounts of ceramic powder (kg) for dental fibers
ceramic_composition = {
    "A1": {"white": 58, "yellow": 38, "pink": 0, "gray": 4},
    "A2": {"white": 91.72, "yellow": 4.5, "pink": 1.28, "gray": 2.5},
    "A3": {"white": 25, "yellow": 75, "pink": 0, "gray": 0},
    "A4": {"white": 9, "yellow": 89, "pink": 1, "gray": 1},
    "A5": {"white": 77.01, "yellow": 15, "pink": 2.99, "gray": 5},
    "B1": {"white": 5, "yellow": 95, "pink": 0, "gray": 0},
    "B2": {"white": 2, "yellow": 88, "pink": 0, "gray": 10},
    "B3": {"white": 35.6, "yellow": 35, "pink": 9.4, "gray": 20},
    "B4": {"white": 51, "yellow": 43, "pink": 0, "gray": 6},
    "C1": {"white": 43, "yellow": 54, "pink": 0, "gray": 3},
    "C2": {"white": 20, "yellow": 80, "pink": 0, "gray": 0},
    "C3": {"white": 0, "yellow": 100, "pink": 0, "gray": 0},
    "C4": {"white": 41, "yellow": 54, "pink": 0, "gray": 5},
    "D2": {"white": 0, "yellow": 88, "pink": 0, "gray": 12},
    "D3": {"white": 24, "yellow": 64, "pink": 0, "gray": 12},
    "D4": {"white": 1, "yellow": 90, "pink": 0, "gray": 9}
}

# Defining the problem
prob = LpProblem("CeramicCostMinimization", LpMinimize)

# Decision variables (how much to use for each implant depending on supplier and material)
x = LpVariable.dicts("x", ((i, s, m) for i in demand for s in costs for m in ceramic_composition[i]), 0, None)

# Penalty variables for over/under production
p_plus = LpVariable.dicts("p_plus", demand.keys(), 0, None)
p_minus = LpVariable.dicts("p_minus", demand.keys(), 0, None)

# Binary variables: Ceramic powder receipt status per supplier
z = LpVariable.dicts("z", ((i, m, s) for i in demand for m in ceramic_composition[i] for s in costs), cat="Binary")

# Objective function: Minimize costs and penalties
prob += lpSum(x[i, s, m] * costs[s][m] for i in demand for s in costs for m in ceramic_composition[i]) + \
        0.02 * lpSum(p_plus[i] for i in demand) + 0.05 * lpSum(p_minus[i] for i in demand)

# Restrictions

# 1. At least one ceramic powder from the 1st supplier must be used for each dental floss.
for i in demand:
    prob += lpSum(x[i, "supplier 1", m] for m in ceramic_composition[i]) >= 1

# 2. For each dental floss, a maximum of two ceramic powders from the 3rd supplier should be used.
for i in demand:
    prob += lpSum(z[i, m, "supplier 3"] for m in ceramic_composition[i]) <= 2

# 3. The amount of each ceramic powder should be the same as the one shown at the beginning
for i in ceramic_composition:
    for m in ceramic_composition[i]:
        prob += lpSum(x[i, s, m] for s in costs) == ceramic_composition[i][m]

# 4. Demand must be met (with over/under production penalty)
for i in demand:
    prob += lpSum(x[i, s, m] for s in costs for m in ceramic_composition[i]) == demand[i] + p_plus[i] - p_minus[i]

# 5. Each ceramic powder should be purchased from only one supplier
for i in demand:
    for m in ceramic_composition[i]:
        prob += lpSum(z[i, m, s] for s in costs) == 1  # Only available from one supplier
        for s in costs:
            prob += x[i, s, m] <= z[i, m, s] * ceramic_composition[i][m]  # Binding with binary variable

# Turn off verbose logging when solving a problem with the CBC solver
prob.solve(PULP_CBC_CMD(msg=False))

# Only show the relationship between ceramic powders and suppliers when drawing conclusions
for i in ceramic_composition:
    print(f"Diş iplementi {i}:")
    for m in ceramic_composition[i]:
        for s in costs:
            if x[i, s, m].varValue != 0:  # Show only non-0
                print(f"  {m.capitalize()} ceramic powder {s} quantity to be purchased: {x[i, s, m].varValue}")
    print()

# Total cost
print(f"Total Cost: {prob.objective.value()}")

# create the table in output format
def generate_formatted_table_with_suppliers(x, ceramic_composition, costs):
    # Table headings
    header = f"{'Dental implantation':<15} | {'White':<10} | {'Yellow':<10} | {'Pink':<10} | {'Gray':<10}\n"
    divider = "_" * 60 + "\n"
    
    # Let's collect the suppliers for each implant and put them in a table format
    formatted_table = header + divider
    for i in ceramic_composition:
        row = [i]  # Dental Implant name
        for m in ceramic_composition[i]:
            found_supplier = False
            for s in costs:
                if x[i, s, m].varValue > 0:  # If this supplier gives quantity
                    row.append(f"supplier {s[-1]}")  # Add supplier
                    found_supplier = True
                    break
            if not found_supplier:
                row.append("0")  # If this material does not exist add 0
        formatted_table += f"{row[0]:<15} | {row[1]:<10} | {row[2]:<10} | {row[3]:<10} | {row[4]:<10}\n"
    
    return formatted_table

# Get the table showing the results
formatted_output = generate_formatted_table_with_suppliers(x, ceramic_composition, costs)
print(formatted_output)
