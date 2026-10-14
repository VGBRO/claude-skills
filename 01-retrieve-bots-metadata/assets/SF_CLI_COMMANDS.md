# Salesforce CLI Commands Reference

Quick reference for SF CLI commands used in Step 1: Bot Metadata Retrieval.

---

## Commands Used in Our Pipeline

### 1. **`sf org list`**
Lists all authenticated Salesforce orgs.

```bash
sf org list --json
```

**Used for:** Checking available orgs and their connection status at pipeline start.

**Output:** JSON with org details (alias, username, instanceUrl, orgId, accessToken).

---

### 2. **`sf org display`**
Shows details about a specific org.

```bash
sf org display --target-org <ORG_ALIAS> --json
```

**Used for:** Getting org ID and instance URL before retrieval.

**Output:** Org metadata including orgId needed for folder naming.

---

### 3. **`sf data query`**
Executes SOQL queries against Salesforce org.

```bash
sf data query --query "<SOQL>" --target-org <ORG_ALIAS> --json
```

**Used for:**
- Listing all bots: `SELECT BotDefinition.DeveloperName, BotDefinition.Description, VersionNumber FROM BotVersion`
- Getting bot version info: `SELECT VersionNumber, Status FROM BotVersion WHERE BotDefinition.DeveloperName = '<BOT_NAME>'`
- Listing ML domains: `SELECT DeveloperName FROM MlDomain`

**Output:** Query results in JSON format.

---

### 4. **`sf project generate`**
Initializes Salesforce DX project structure.

```bash
sf project generate --name <PROJECT_NAME>
```

**Used for:** Creating `sfdx-project.json` if it doesn't exist (project setup).

**Output:** Creates project configuration files.

---

### 5. **`sf project retrieve start`**
Retrieves metadata from Salesforce org.

```bash
sf project retrieve start --metadata "<TYPE>:<NAME>" --target-org <ORG_ALIAS>
```

**Used for:**
- Retrieving bot metadata: `--metadata "Bot:<BOT_NAME>"`
- Retrieving ML domains: `--metadata "MlDomain:<DOMAIN_NAME>"`

**What it retrieves:**
- **Bot**: `main/default/bots/<BotName>/<BotName>.bot-meta.xml` + `v*.botVersion-meta.xml`
- **MlDomain**: `main/default/mlDomains/<DomainName>.mlDomain-meta.xml`

**Output:** XML metadata files in `force-app/main/default/` or configured package directory.

---

## Authentication

### Login to Org
```bash
# Production/Developer org
sf org login web --alias <ALIAS>

# Sandbox
sf org login web --alias <ALIAS> --instance-url https://test.salesforce.com

# Orgfarm (Salesforce internal)
sf org login web --alias <ALIAS> --instance-url https://orgfarm-xxxx.test1.my.pc-rnd.salesforce.com/
```

### Logout
```bash
sf org logout --target-org <ALIAS>
```

---

## Common Queries

### List All Bots
```bash
sf data query \
  --query "SELECT BotDefinition.DeveloperName, BotDefinition.Description, VersionNumber, LastModifiedDate FROM BotVersion ORDER BY BotDefinition.DeveloperName, VersionNumber DESC" \
  --target-org <ORG_ALIAS>
```

### List ML Domains
```bash
sf data query \
  --query "SELECT DeveloperName, Label FROM MlDomain" \
  --target-org <ORG_ALIAS>
```

### Get Bot Version Details
```bash
sf data query \
  --query "SELECT VersionNumber, Status, LastModifiedDate FROM BotVersion WHERE BotDefinition.DeveloperName = '<BOT_NAME>' ORDER BY VersionNumber DESC" \
  --target-org <ORG_ALIAS>
```

---

## Typical Workflow

```bash
# 1. List connected orgs
sf org list

# 2. Get org details
sf org display --target-org my-org --json

# 3. List bots in org
sf data query \
  --query "SELECT BotDefinition.DeveloperName FROM BotVersion" \
  --target-org my-org

# 4. Retrieve bot metadata
sf project retrieve start \
  --metadata "Bot:MyBot" \
  --target-org my-org

# 5. Retrieve ML domain (if bot uses Intent Sets)
sf project retrieve start \
  --metadata "MlDomain:IntentSets" \
  --target-org my-org

# 6. Verify retrieved files
ls -la force-app/main/default/bots/MyBot/
ls -la force-app/main/default/mlDomains/
```

---

## Troubleshooting

### "Entity of type 'Bot' named 'X' cannot be found"
- Bot doesn't exist or wrong name
- Use exact `DeveloperName` (case-sensitive)
- List bots first to verify name

### "Entity of type 'MlDomain' named 'X' cannot be found"
- ML domain doesn't exist or wrong name
- Common names: `IntentSets`, `Intents`, `<BotName>Intents`
- List ML domains first: `sf data query --query "SELECT DeveloperName FROM MlDomain"`

### "No org configuration found"
- Not authenticated: `sf org login web --alias my-org`

### "This command requires a username"
- No default org set
- Always use `--target-org <ALIAS>`

---

## Quick Reference

| Task | Command |
|------|---------|
| List orgs | `sf org list` |
| Org details | `sf org display --target-org <ORG>` |
| List bots | `sf data query --query "SELECT DeveloperName FROM BotVersion" --target-org <ORG>` |
| Retrieve bot | `sf project retrieve start --metadata "Bot:<NAME>" --target-org <ORG>` |
| Retrieve ML domain | `sf project retrieve start --metadata "MlDomain:IntentSets" --target-org <ORG>` |
| Query SOQL | `sf data query --query "<SOQL>" --target-org <ORG>` |

---

## Best Practices

1. ✅ **Always specify `--target-org`** - Even with a default org, be explicit
2. ✅ **Use meaningful aliases** - `prod-org`, `dev-org`, `staging-org`
3. ✅ **Verify names first** - List bots/domains before retrieval
4. ✅ **Use `DeveloperName`** - Not `MasterLabel` (labels can have spaces/special chars)
5. ✅ **Add `--json` flag** - For programmatic parsing in scripts
6. ✅ **Check retrieved files** - Verify XML files exist after retrieval

---

## Notes

- SF CLI version 2.0+ required (use `sf --version` to check)
- Commands use `sf` (not legacy `sfdx`)
- Network access required to Salesforce orgs
- Large bots may take 30-60 seconds to retrieve
- ML domains are optional but needed for complete training data

---

## Resources

- [SF CLI Command Reference](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm)
- [Metadata API: Bot](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_bot.htm)
- [Metadata API: MlDomain](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_mldomain.htm)
