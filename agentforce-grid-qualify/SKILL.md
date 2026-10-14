---
name: agentforce-grid-qualify
description: >
  Qualifies a customer account as a candidate for CS-assisted Agentforce Grid adoption.
  Researches the account across Slack, Gmail, and Google Drive to find internal signals
  about their Grid usage, why they went quiet, and who owns the relationship. Produces
  a qualification brief formatted for Slack. Use when you want to assess whether an
  account from the Agentforce Grid usage dataset is worth a CS re-engagement conversation.
metadata:
  author: salesforce-cs
  version: "2.0"
compatibility: Requires Slack, Gmail, and Google Drive MCP tools. Usage dataset at /Users/vguruvugari/Downloads/AgF GRID CUSTOMERS 2026 - Main.csv
---

# Agentforce Grid Account Qualification

## What this skill does

Research a named Salesforce customer to determine whether they are a strong candidate for
CS-assisted Agentforce Grid re-engagement — deploying or expanding Grid workbooks with
hands-on CS support.

## Who this is for

Customers in the Warm, Cooling, or Cold tiers of the Agentforce Grid usage dataset who had
≥ 100 cell runs. These accounts had a real use case and went quiet. The question is whether
CS can help them unlock more value.

---

## Trigger detection

Extract the account name from any of these patterns:
- `/grid-qualify <account name>`
- `qualify <account name> for grid`
- `grid qualify <account name>`
- `qualify <account name>`
- `check <account name> for grid`

If no account name is clear, ask: *"Which account should I check for Agentforce Grid re-engagement?"*

---

## Step 1 — Look up the account in the usage dataset

Load: `/Users/vguruvugari/Downloads/AgF GRID CUSTOMERS 2026 - Main.csv`

Find the row matching the account name (fuzzy match if needed). Extract:
- **Org ID**
- **Account Name**
- **Last Activity** (date)
- **Cell Runs** (total)
- **Tier** (Warm / Cooling / Cold)

If not found, say so and proceed with research using the account name alone.

If multiple rows match, list them and ask which one.

---

## Step 2 — Research the account

Search ALL connected sources. Run multiple queries per source before forming conclusions.
Capture exact quotes, source (channel/sender/file), and approximate date for every signal found.

### Slack — search for:
- `<account name> grid`
- `<account name> agentforce grid`
- `<account name> workbook`
- `<account name> cell runs`
- `<account name> agentforce`
- `<account name> AI`
- `<account name> account enrichment`
- `<account name> sales intelligence`
- `<account name> use case`
- `<account name> blocked OR blocker OR stuck`
- `<account name> license OR entitlement`
- `<account name> renewal OR contract`
- `<account name> AE OR "account executive"`
- `<account name> CSM OR "customer success"`
- `<account name> QBR OR "business review"`
- `<account name> champion OR sponsor`

### Gmail — same query set as Slack

### Google Drive — search for:
- `<account name>`
- `<account name> grid`
- `<account name> agentforce`
- `<account name> account plan`
- `<account name> QBR`
- `<account name> success plan`
- `<account name> adoption`

### OrgCS / org62 — SOQL lookup

Look up the account in OrgCS first. If not found, try org62 (alias: `org62` — re-auth required if expired).

```soql
SELECT Name, L1_Success_Cloud__c, CSM__c, Org62_AccountOwner__c,
       SAE_Overlay__c, Account_Owner_Role__c
FROM Account
WHERE Name LIKE '%<account name>%'
LIMIT 5
```

Extract:
- **Success Plan** — `L1_Success_Cloud__c` (Signature / Premier / Standard / null)
- **CSM** — `CSM__c`
- **AE / Account Owner** — `Org62_AccountOwner__c`
- **SAE Overlay** — `SAE_Overlay__c`
- **Owner Role** — `Account_Owner_Role__c`

If org62 is expired, note it in the brief and instruct the user to run:
`sf org login web --alias org62` then re-run the qualification.

---

## Step 3 — Score the account

Start at 0. Add points based on evidence found:

| Signal | Points |
|--------|--------|
| Cell runs ≥ 5,000 | +30 |
| Cell runs 500–4,999 | +20 |
| Cell runs 100–499 | +10 |
| Last active within 60 days (Warm) | +25 |
| Last active 61–120 days (Cooling) | +15 |
| Last active > 120 days (Cold) | +5 |
| Known use case identified from research | +20 |
| Blocker identified (specific, fixable) | +15 |
| Active AE/CSM relationship confirmed | +15 |
| Champion or internal sponsor identified | +10 |
| AI roadmap interest expressed | +10 |
| Agentforce license confirmed | +10 |
| No internal context found | −15 |
| Relationship appears fully dark (no response to CS/AE) | −15 |
| Budget or contract blocker (hard stop) | −20 |

**Labels:**
- 75–100 → Strong Re-engagement Candidate
- 50–74 → Likely Candidate
- 25–49 → Needs Qualification
- 1–24 → Weak Signal
- 0 → Insufficient Data

**Recommendation logic:**
- Score ≥ 75 + known use case → **Engage Now** — offer live deployment session this week
- Score ≥ 50 OR blocker identified → **Develop & Return** — get AE/CSM context first
- Score ≥ 25 → **Monitor** — flag for AE awareness, no direct CS action yet
- Score < 25 → **Insufficient Data** — check with owning CSM before proceeding

---

## Step 4 — What to look for (signal guide)

### Grid usage signals (primary)
- What were they building? Account enrichment, RevOps next steps, SMS outreach, service sentiment — or something custom?
- How were they using it? Bulk runs suggest production use; low runs suggest exploration
- Did cell run volume grow then stop, or was it steady? Growth-then-stop = specific event caused the drop

### Drop-off signals (why they went quiet)
- Blocker mentions: permissions, Einstein not enabled, Grid Studio access, missing licenses
- Contract or budget discussions around the time they stopped
- Org changes: new admin, reorg, champion left the company
- Competing priority: a larger initiative crowded Grid out
- Technical issue: API errors, data quality problems, prompt issues

### Relationship signals
- AE or CSM name mentioned in Slack/email
- Recent QBR or account plan — signals active relationship
- Any CS-initiated outreach since they went quiet — and whether it got a response
- Champion or power user named — someone who was excited and drove adoption internally

### Expansion signals
- Use case that maps to the four demo grids (Account, Opportunity, Lead, Case)
- Requests for more Grid features, more columns, more rows
- Mentions of wanting to share grids with their team or scale usage

### Risk signals (lower the score)
- "We're evaluating other tools" — competitive risk
- Legal or compliance concerns about AI-generated content
- IT governance issues with external AI tools
- Budget freeze or contract renewal pending

---

## Step 5 — Produce the qualification brief

Post as a single Slack message using Slack markdown. Use this exact structure:

```
[score emoji] *Agentforce Grid Re-engagement Brief: <Account Name>*
_Researched <date> · Sources: <sources searched>_
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Executive Summary*
<2-3 sentences: what were they doing with Grid, when did they stop, are they a re-engagement candidate>

*Grid Usage*
📊 *<cell runs> cell runs* · Last active: <date> · Tier: <tier>

*Qualification Score*
[emoji] *<score>/100* — <label>

*Recommendation*
[emoji] *<Engage Now | Develop & Return | Monitor | Insufficient Data>*
<1-sentence rationale>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Usage & Drop-off Signals*

[✅ or ❌] *Known Use Case*  [● high | ◐ medium | ○ low | – unknown]
  › _<what they were building — or "Use case unknown — check with AE/CSM">_

[✅ or ❌] *Drop-off Reason Identified*  [confidence]
  › _<what caused them to stop — or "No drop-off signal found internally">_

[✅ or ❌] *Active AE/CSM Relationship*  [confidence]
  › _<AE/CSM name and evidence — or "Not found">_

[✅ or ❌] *Champion / Internal Sponsor*  [confidence]
  › _<name and role — or "Not identified">_

[✅ or ❌] *Agentforce License*  [confidence]
  › _<evidence — or "Unknown">_

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Context Signals* _(useful for conversation angle)_
• <signal — e.g. AI roadmap interest, QBR mention, expansion request, competitor comparison>
_<or "No additional context found">_

*Account Team* _(from OrgCS / org62)_
👤 *AE:* <Org62_AccountOwner__c — or "Not found">
👤 *CSM:* <CSM__c — or "Not found">
👤 *SAE Overlay:* <SAE_Overlay__c — or "Not found">
🏅 *Success Plan:* <L1_Success_Cloud__c — Signature / Premier / Standard / Unknown>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Recommended Next Steps*
1. <action>
2. <action>
3. <action>

*Suggested Outreach Message* _(to send to AE/CSM)_
> Hey [Name],
>
> I'm looking at Agentforce Grid usage data and noticed <Account Name> had <X> cell runs
> but has been inactive since <Month>. <One sentence about what they were likely doing based on research>.
>
> Do you have context on what happened there? We have hands-on resources that might help
> if they hit a blocker — happy to jump on a quick call if useful.
>
> Thanks

_Powered by Agentforce Grid CS Intelligence · Salesforce CS · Data from Slack, Gmail, Drive_
```

**Score emoji key:**
- 🟢 score ≥ 75
- 🟡 score 50–74
- 🟠 score 25–49
- 🔴 score < 25

**Recommendation emoji key:**
- 🚀 Engage Now
- 🔧 Develop & Return
- 👁️ Monitor
- ❓ Insufficient Data

---

## Step 6 — Edge cases

**No internal data found:** Post the brief with score based on cell runs + recency only. Add:
*"No internal context found. Recommend checking with owning CSM/AE before outreach."*

**Hard blocker identified (budget/contract):** Flag clearly. Recommend: *"Hold until contract situation resolves. Flag for AE awareness."*

**Account team not found:** Note it explicitly. The outreach message becomes harder to personalize — suggest CS find the AE via Salesforce CRM before sending.

**Multiple accounts match the name:** List up to 3 matches with their Org IDs and ask: *"Which account did you mean?"*

---

## Step 7 — After the brief

Ask:
- *"Qualify another account?"* → repeat from Step 1
- *"Run the top 20?"* → process top 20 accounts from Warm + Cooling + Cold with ≥ 100 cell runs, sorted by cell runs descending, produce a summary table first then full briefs on request
- *"Done"* → summarize counts by recommendation label (Engage Now / Develop & Return / Monitor / Insufficient Data)
