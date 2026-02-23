# Azure OpenAI & Cognitive Services — Cross‑Subscription Metrics Workbook

An [Azure Monitor Workbook](https://learn.microsoft.com/azure/azure-monitor/visualize/workbooks-overview) that provides a **single pane of glass** for monitoring Azure OpenAI (including PTU deployments) and Cognitive Services metrics across **multiple Azure subscriptions**.

## Why This Workbook?

When Azure Cognitive Services resources are spread across many subscriptions, monitoring them consistently is difficult:

- **Log Analytics gaps** — metrics may be ingested into different Log Analytics Workspaces, and some resources may have no workspace configured at all, leading to incomplete data.
- **No single dashboard** — the Azure portal shows metrics per‑resource; there is no built‑in cross‑subscription view.

This workbook solves both problems by querying **Azure Monitor platform metrics directly**. Platform metrics are emitted automatically by every Cognitive Services resource — no diagnostic settings, no Log Analytics Workspace, and no additional configuration required.

## Features

| Section | Description |
|---|---|
| **Resource Inventory** | Azure Resource Graph grid listing every `microsoft.cognitiveservices/accounts` resource across selected subscriptions |
| **PTU Utilization** | `ProvisionedManagedUtilizationV2` — percentage of provisioned‑managed capacity consumed (PTU deployments only) |
| **Azure OpenAI Requests** | `AzureOpenAIRequests` — total Azure OpenAI API request count |
| **Total Calls** | `TotalCalls` — total API calls across all Cognitive Services resource types |
| **Token Usage** | `ProcessedPromptTokens`, `GeneratedTokens`, `TokenTransaction` — input/output token volume (Azure OpenAI) |
| **Success vs Errors** | `SuccessfulCalls`, `TotalErrors`, `BlockedCalls` |
| **Latency** | `Latency` — average end‑to‑end latency in milliseconds |
| **Server & Client Errors** | `ServerErrors`, `ClientErrors` |
| **Data Transfer** | `DataIn`, `DataOut` — bytes received and sent |

All metric names are sourced from the [official supported metrics reference](https://learn.microsoft.com/azure/azure-monitor/reference/supported-metrics/microsoft-cognitiveservices-accounts-metrics).

## Parameters

The workbook exposes the following interactive parameters at the top:

| Parameter | Description |
|---|---|
| **Subscriptions** | Multi‑select picker for Azure subscriptions (defaults to all) |
| **Resource Groups** | Multi‑select dropdown filtered to groups that contain Cognitive Services resources |
| **Cognitive Services Resources** | Multi‑select resource picker filtered by the above selections |
| **Time Range** | Standard time range selector (1 hour to 30 days, plus custom) |
| **Aggregation** | Time grain for metric roll‑up (1 min – 1 day) |

## Prerequisites

### Permissions

| Scope | Role | Reason |
|---|---|---|
| Each subscription you want to monitor | **Reader** (or higher) | Required to discover resources via Azure Resource Graph and to read Azure Monitor metrics |

No additional roles are needed. Because the workbook uses platform metrics (not Log Analytics), there is no requirement for Log Analytics Workspace access.

### Configuration

**None.** Platform metrics for Cognitive Services are emitted automatically. You do **not** need to:

- Create or configure a Log Analytics Workspace
- Enable diagnostic settings on each resource
- Install any agents

> **Note:** If you also want log‑level data (e.g., per‑request details), you can separately enable diagnostic settings to send logs to a Log Analytics Workspace, but this is *not* required for the metrics shown in this workbook.

## Deployment

### Option 1 — Azure Portal (Import JSON)

1. Open the [Azure portal](https://portal.azure.com).
2. Navigate to **Monitor → Workbooks**.
3. Click **+ New**.
4. Click the **Advanced Editor** (`</>`) button on the toolbar.
5. Replace the contents with the JSON from [`workbooks/CognitiveServicesOverview.workbook`](workbooks/CognitiveServicesOverview.workbook).
6. Click **Apply**, then **Done Editing**, then **Save**.

### Option 2 — ARM Template (CLI)

```bash
az deployment group create \
  --resource-group <your-resource-group> \
  --template-file deploy/azuredeploy.json \
  --parameters deploy/azuredeploy.parameters.json
```

### Option 3 — ARM Template (PowerShell)

```powershell
New-AzResourceGroupDeployment `
  -ResourceGroupName <your-resource-group> `
  -TemplateFile deploy/azuredeploy.json `
  -TemplateParameterFile deploy/azuredeploy.parameters.json
```

## Repository Structure

```
├── workbooks/
│   └── CognitiveServicesOverview.workbook   # Workbook JSON definition
├── deploy/
│   ├── azuredeploy.json                     # ARM template
│   └── azuredeploy.parameters.json          # ARM template parameters
└── README.md                                # This file
```

## Extending the Workbook

- **Add more metrics** — edit the `.workbook` file and add new `type: 10` (Metrics) items referencing any metric from the [supported metrics list](https://learn.microsoft.com/azure/azure-monitor/reference/supported-metrics/microsoft-cognitiveservices-accounts-metrics).
- **Add other resource types** — duplicate a metrics section and change `resourceType` and the parameter queries to target a different Azure resource type.
- **Re‑generate the ARM template** — after editing the workbook JSON, update the `serializedData` field in `deploy/azuredeploy.json` with the minified workbook JSON string.

## License

This project is provided as‑is under the [MIT License](LICENSE).
