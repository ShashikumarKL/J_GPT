from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import subprocess


app = FastAPI(title="Jenkins Pipeline Generator")

template_dir = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))
template = env.get_template("Jenkinsfile.j2")

pipelines: Dict[str, Dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    name: str
    tech_stack: List[str] = []
    requirements: str


def detect_tech_stack(requirements: str) -> List[str]:
    requirements_lower = requirements.lower()
    detected = []
    for tech in [
        "docker",
        "artifactory",
        "cmake",
        "make",
        "ghs",
        "bat",
        "sh",
    ]:
        if tech in requirements_lower:
            detected.append(tech)
    return detected


def validate_jenkinsfile(jenkinsfile: str) -> tuple[bool, str]:
    """Validate Jenkinsfile syntax using jenkins-cli or a Groovy parser.

    Attempts to validate the provided Jenkinsfile by first invoking
    ``jenkins-cli declarative-linter``. If the CLI is unavailable, it falls
    back to calling a local ``groovy`` executable. Syntax errors from either
    tool are captured and returned to the caller.

    Returns
    -------
    tuple[bool, str]
        A tuple where the boolean indicates whether the Jenkinsfile is valid
        and the string contains any error message produced by the validator.
    """

    cmds = [
        ("jenkins-cli", ["jenkins-cli", "declarative-linter"], True),
        ("groovy", ["groovy", "-"], False),
    ]

    for name, cmd, use_stdin in cmds:
        try:
            subprocess.run(
                cmd,
                input=jenkinsfile if use_stdin else None,
                capture_output=True,
                text=True,
                check=True,
            )
            return True, ""
        except FileNotFoundError:
            continue  # Tool not installed; try next option
        except subprocess.CalledProcessError as e:
            error_msg = (e.stderr or e.stdout).strip()
            return False, error_msg

    raise HTTPException(
        status_code=500, detail="No Jenkinsfile validator available"
    )


@app.post("/generate")
def generate_pipeline(req: GenerateRequest):
    tech_stack = list({*req.tech_stack, *detect_tech_stack(req.requirements)})
    jenkinsfile = template.render(name=req.name, tech_stack=tech_stack)
    is_valid, error_msg = validate_jenkinsfile(jenkinsfile)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    pipeline_id = str(uuid4())
    pipelines[pipeline_id] = {
        "id": pipeline_id,
        "name": req.name,
        "tech_stack": tech_stack,
        "requirements": req.requirements,
        "created_at": datetime.utcnow().isoformat(),
        "jenkinsfile": jenkinsfile,
    }
    return {"pipeline_id": pipeline_id, "jenkinsfile": jenkinsfile}


@app.get("/list")
def list_pipelines():
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "tech_stack": p["tech_stack"],
            "created_at": p["created_at"],
        }
        for p in pipelines.values()
    ]


@app.get("/export/{pipeline_id}")
def export_pipeline(pipeline_id: str):
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    filename = f"{pipeline['name']}.jenkinsfile"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(content=pipeline["jenkinsfile"], media_type="text/plain", headers=headers)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
