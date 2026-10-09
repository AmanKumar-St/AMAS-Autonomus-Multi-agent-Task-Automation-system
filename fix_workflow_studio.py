with open(r'E:\Projects\AMAS\AMAS-Autonomus-Multi-agent-Task-Automation-system\src\components\WorkflowStudio.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace hardcoded fallbacks in disaster section
replacements = [
    ('{pm.deaths_reported || "92+ Deaths"}', '{pm.deaths_reported || "Data unavailable"}'),
    ('{pm.deaths_detail || "Multi-state confirmed casualties"}', '{pm.deaths_detail || "No detail available"}'),
    ('{pm.relief_funds_allocated || "\u20b9180+ Crore"}', '{pm.relief_funds_allocated || "Data unavailable"}'),
    ('{pm.relief_funds_detail || "SDRF & emergency rescue funding"}', '{pm.relief_funds_detail || "No detail available"}'),
    ('{pm.infrastructure_impact || "24K+ Homes & 5K+ Roads"}', '{pm.infrastructure_impact || "Data unavailable"}'),
    ('{pm.infrastructure_detail || "Houses, highways & water supply"}', '{pm.infrastructure_detail || "No detail available"}'),
    ('3.3+ Lakh', '{pm.affected_population || "Data unavailable"}'),
    ('{pm.affected_population || "People displaced / in relief camps"}', '{pm.affected_population || "No detail available"}'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(r'E:\Projects\AMAS\AMAS-Autonomus-Multi-agent-Task-Automation-system\src\components\WorkflowStudio.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacements done")