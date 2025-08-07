from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader
from uuid import uuid4
from datetime import datetime

app = FastAPI(title="Jenkins Pipeline Generator")

env = Environment(loader=FileSystemLoader("templates"))
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


def validate_jenkinsfile(jenkinsfile: str) -> bool:
    # Stub for syntax validation
    return True


@app.post("/generate")
def generate_pipeline(req: GenerateRequest):
    tech_stack = list({*req.tech_stack, *detect_tech_stack(req.requirements)})
    jenkinsfile = template.render(name=req.name, tech_stack=tech_stack)
    if not validate_jenkinsfile(jenkinsfile):
        raise HTTPException(status_code=400, detail="Invalid Jenkinsfile syntax")

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
