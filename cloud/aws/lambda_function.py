import json
import os
import urllib.error
import urllib.request

import boto3

ssm = boto3.client("ssm")

def lambda_handler(event, context):
    slot = str(event.get("slot", "manual"))
    token = ssm.get_parameter(Name=os.environ["GITHUB_TOKEN_PARAMETER"], WithDecryption=True)["Parameter"]["Value"]
    owner = os.environ["GITHUB_OWNER"]
    repository = os.environ["GITHUB_REPOSITORY"]
    workflow = os.environ.get("GITHUB_WORKFLOW", "amala-cloud-office.yml")
    branch = os.environ.get("GITHUB_BRANCH", "main")
    url = f"https://api.github.com/repos/{owner}/{repository}/actions/workflows/{workflow}/dispatches"
    payload = json.dumps({"ref": branch, "inputs": {"slot": slot}}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST", headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "amala-aws-scheduler/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"GitHub dispatch failed with HTTP {error.code}: {body}") from error
    if status != 204:
        raise RuntimeError(f"GitHub dispatch returned unexpected HTTP {status}")
    return {"statusCode": 200, "body": json.dumps({"dispatched": True, "slot": slot})}
