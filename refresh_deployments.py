"""
Refresh model deployment data from the ARM API and inject into workbook parameters.
Also syncs the workbook into the ARM template.

Usage:
    python refresh_deployments.py
"""
import json
import subprocess
import sys

WORKBOOK_PATH = "workbooks/CognitiveServicesOverview.workbook"
ARM_PATH = "deploy/azuredeploy.json"


def run_az(args):
    """Run an az CLI command and return parsed JSON."""
    result = subprocess.run(
        ["az"] + args + ["-o", "json"],
        capture_output=True, text=True, shell=True
    )
    if result.returncode != 0:
        print(f"ERROR: az {' '.join(args)}\n{result.stderr}", file=sys.stderr)
        return None
    return json.loads(result.stdout) if result.stdout.strip() else None


def get_all_deployments():
    """List every deployment across all Cognitive Services accounts."""
    accounts = run_az(["cognitiveservices", "account", "list"])
    if not accounts:
        print("No Cognitive Services accounts found.", file=sys.stderr)
        return []

    deployments = []
    for acct in accounts:
        name = acct["name"]
        rg = acct["resourceGroup"]
        deps = run_az([
            "cognitiveservices", "account", "deployment", "list",
            "--name", name, "--resource-group", rg
        ])
        if deps:
            for d in deps:
                model = d.get("properties", {}).get("model", {})
                deployments.append({
                    "deploymentName": d["name"],
                    "accountName": name,
                    "resourceGroup": rg,
                    "modelName": model.get("name", ""),
                    "modelVersion": model.get("version", ""),
                    "modelFormat": model.get("format", ""),
                    "skuName": d.get("sku", {}).get("name", ""),
                    "skuCapacity": d.get("sku", {}).get("capacity", 0),
                })
    return deployments


def build_model_name_json(deployments):
    """Build jsonData for the ModelName dropdown."""
    models = sorted(set(d["modelName"] for d in deployments if d["modelName"]))
    return json.dumps([
        {"value": m, "label": m, "selected": True}
        for m in models
    ])


def build_deployment_json(deployments):
    """Build jsonData for the ModelDeploymentName dropdown (grouped by model)."""
    items = []
    for d in sorted(deployments, key=lambda x: (x["modelName"], x["deploymentName"])):
        items.append({
            "value": d["deploymentName"],
            "label": f"{d['deploymentName']}  ({d['accountName']})",
            "selected": True,
            "group": d["modelName"] or "Unknown"
        })
    return json.dumps(items)


def update_workbook(deployments):
    """Patch the workbook parameters to use jsonData instead of ARG queries."""
    with open(WORKBOOK_PATH, "r", encoding="utf-8") as f:
        wb = json.load(f)

    model_json = build_model_name_json(deployments)
    deploy_json = build_deployment_json(deployments)

    # Find the parameters step
    for item in wb["items"]:
        if item.get("name") == "parameters" and item.get("type") == 9:
            params = item["content"]["parameters"]
            for p in params:
                if p.get("name") == "ModelName":
                    # Switch from ARG query to static jsonData
                    p["jsonData"] = model_json
                    # Remove ARG-specific fields
                    for key in ["query", "queryType", "resourceType", "crossComponentResources"]:
                        p.pop(key, None)
                    print(f"  ModelName: {len(json.loads(model_json))} models")

                elif p.get("name") == "ModelDeploymentName":
                    # Switch from ARG query to static jsonData
                    p["jsonData"] = deploy_json
                    # Remove ARG-specific fields
                    for key in ["query", "queryType", "resourceType", "crossComponentResources"]:
                        p.pop(key, None)
                    print(f"  ModelDeploymentName: {len(json.loads(deploy_json))} deployments")

    with open(WORKBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(wb, f, indent=2)
    print(f"Updated {WORKBOOK_PATH}")


def sync_arm():
    """Sync workbook JSON into ARM template serializedData."""
    with open(WORKBOOK_PATH, "r", encoding="utf-8") as f:
        wb = json.load(f)
    with open(ARM_PATH, "r", encoding="utf-8") as f:
        arm = json.load(f)
    arm["resources"][0]["properties"]["serializedData"] = json.dumps(wb)
    with open(ARM_PATH, "w", encoding="utf-8") as f:
        json.dump(arm, f, indent=2)
    print(f"Synced {ARM_PATH}")


if __name__ == "__main__":
    print("Querying ARM API for all Cognitive Services deployments...")
    deployments = get_all_deployments()
    print(f"Found {len(deployments)} deployments total:")
    for d in deployments:
        print(f"  {d['accountName']}/{d['deploymentName']} -> {d['modelName']} v{d['modelVersion']} ({d['skuName']})")

    print("\nUpdating workbook parameters...")
    update_workbook(deployments)

    print("\nSyncing ARM template...")
    sync_arm()

    print("\nDone. Run the following to deploy:")
    print('  az deployment group create --resource-group rg-apim-mcp-aks-2 --template-file "deploy\\azuredeploy.json" --parameters "deploy\\azuredeploy.parameters.json"')
