#!/usr/bin/env python3
"""Disposable fixture recipe. Refuses resources outside a named local rehearsal."""
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

project = os.environ["CODITY_DEPLOY_PROJECT"]
resource = os.environ["CODITY_DEPLOY_RESOURCE"]
endpoint = os.environ["DOCKER_HOST"]
if not project.startswith("codity-deploy-test-") or resource != "app" or not endpoint.startswith("unix:///"):
    raise RuntimeError("Only the isolated local deployment fixture is supported")
name = project + "-" + resource
port = os.environ["CODITY_DEPLOY_PORT"]

def docker(*args):
    return subprocess.check_output(["docker", "--host", endpoint, *args], stderr=subprocess.DEVNULL)

def current():
    item = json.loads(docker("inspect", name))[0]
    if item["Config"]["Labels"].get("codity.deployment.fixture") != project:
        raise RuntimeError("Resource is not this fixture")
    return item

phase = sys.argv[1]
if phase == "preflight":
    current()
elif phase in {"deploy", "rollback"}:
    old = current()
    revision = os.environ["CODITY_DEPLOY_REVISION"] if phase == "deploy" else os.environ["CODITY_PRIOR_REVISION"]
    artifact = os.environ["CODITY_ARTIFACT_DIGEST"] if phase == "deploy" else old["Config"]["Labels"]["codity.fixture.prior_artifact"]
    prior_artifact = old["Config"]["Labels"]["codity.fixture.artifact"] if phase == "deploy" else old["Config"]["Labels"]["codity.fixture.prior_artifact"]
    mode = old["Config"]["Labels"].get("codity.fixture.mode", "healthy")
    if phase == "deploy" and mode == "disconnect":
        time.sleep(30)
    unhealthy = (phase == "deploy" and mode in {"unhealthy", "rollback-failed"}) or (phase == "rollback" and mode == "rollback-failed")
    greeting = "broken" if phase == "deploy" and mode == "feature-broken" else "Hello from the reviewed PR"
    server = (
        "const http=require('http');http.createServer((q,s)=>{"
        "s.setHeader('Content-Type','application/json');"
        "s.statusCode=" + ("503" if unhealthy else "200") + ";"
        "s.end(JSON.stringify(q.url==='/greeting'?{message:" + json.dumps(greeting) + "}:"
        "{revision:" + json.dumps(revision) + ",artifact:" + json.dumps(artifact) + "}));"
        "}).listen(8080,'0.0.0.0');"
    )
    docker("rm", "-f", name)
    docker("run", "-d", "--name", name, "--label", "codity.deployment.fixture=" + project, "--label", "codity.deployment.resource=app", "--label", "codity.fixture.revision=" + revision, "--label", "codity.fixture.artifact=" + artifact, "--label", "codity.fixture.prior_artifact=" + prior_artifact, "--label", "codity.fixture.mode=" + mode, "-p", "127.0.0.1:" + port + ":8080", "--entrypoint", "node", "scanner-node:20", "-e", server)
elif phase == "inspect":
    item = current()
    labels = item["Config"]["Labels"]
    print(json.dumps({"revision": labels["codity.fixture.revision"], "artifact_digest": labels["codity.fixture.artifact"], "resource_digest": hashlib.sha256(item["Id"].encode()).hexdigest()}))
elif phase in {"health", "smoke"}:
    error = None
    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:" + port + ("/greeting" if phase == "smoke" else "/health"), timeout=1) as response:
                body = json.load(response)
                if response.status == 200 and (phase == "health" or body.get("message") == "Hello from the reviewed PR"):
                    sys.exit(0)
        except Exception as failure:
            error = failure
        time.sleep(0.1)
    raise RuntimeError("Fixture health check failed") from error
else:
    raise RuntimeError("Unknown fixture phase")
