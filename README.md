# J_GPT


J_GPT combines a FastAPI service for generating Jenkins pipelines with a simple Jenkins plugin.

## FastAPI service
The FastAPI app exposes endpoints to generate and manage Jenkinsfiles based on a project's requirements. It renders a Jenkinsfile from `templates/Jenkinsfile.j2` and supports basic tech‑stack detection.

### Setup
```bash
pip install -r requirements.txt
```

### Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Endpoints:
- `POST /generate` – create a Jenkinsfile from a name, tech stack and requirement description
- `GET /list` – list previously generated pipelines
- `GET /export/{pipeline_id}` – download a generated Jenkinsfile

## Jenkins plugin
The Jenkins plugin adds a **ChatGPT Builder** step that prints a configured prompt during a build.

### Build
```bash
mvn package
```
The compiled plugin is created at `target/chatgpt.hpi`.

### Configure
1. Upload the HPI in Jenkins via **Manage Jenkins → Plugins → Advanced → Upload Plugin**.
2. In a job, add the **ChatGPT Builder** build step and set the *Prompt* field.

