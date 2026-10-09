with open(r'E:\Projects\AMAS\AMAS-Autonomus-Multi-agent-Task-Automation-system\src\components\WorkflowStudio.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace hardcoded sources fallbacks
replacements = [
    ('Sources Audited: {(comp.sources_audited || ["Cricbuzz", "ESPN", "Sports Wire"]).join(" \u2022 ")}', 'Sources Audited: {(comp.sources_audited || []).join(" \u2022 ") || "No sources available"}'),
    ('Sources Audited: {(comp.sources_audited || ["Variety", "The Hollywood Reporter", "Box Office Mojo"]).join(" \u2022 ")}', 'Sources Audited: {(comp.sources_audited || []).join(" \u2022 ") || "No sources available"}'),
    ('Sources Audited: {(comp.sources_audited || ["Space.com", "NASA Announcements", "Aerospace Telemetry"]).join(" \u2022 ")}', 'Sources Audited: {(comp.sources_audited || []).join(" \u2022 ") || "No sources available"}'),
    ('Sources Audited: {(comp.sources_audited || ["The Times of India", "The Indian Express", "The New Indian Express", "The Statesman"]).join(" \u2022 ")}', 'Sources Audited: {(comp.sources_audited || []).join(" \u2022 ") || "No sources available"}'),
    ('Sources Audited: {comp.sources_audited.join(" \u2022 ")}', 'Sources Audited: {(comp.sources_audited || []).join(" \u2022 ") || "No sources available"}'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(r'E:\Projects\AMAS\AMAS-Autonomus-Multi-agent-Task-Automation-system\src\components\WorkflowStudio.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Sources fallbacks replacements done')