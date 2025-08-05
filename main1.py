from fastapi import FastAPI, HTTPException
from env_request_schemas import EnvRequestCreate
from env_request_service import create_env_request, get_all_env_requests, get_env_request_by_id
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/env-request")
def create_env(data: EnvRequestCreate):
    request_id = create_env_request(data)
    return {"request_id": request_id, "message": "Saved successfully"}

@app.get("/env-request")
def list_envs():
    return get_all_env_requests()

@app.get("/env-request/{request_id}")
def get_env(request_id: str):
    env = get_env_request_by_id(request_id)
    if env:
        return env.attribute_values
    raise HTTPException(status_code=404, detail="Not found")

# Main entry point
if __name__ == "__main__":
    uvicorn.run("your_module_name:app", host="0.0.0.0", port=8000, reload=True)
