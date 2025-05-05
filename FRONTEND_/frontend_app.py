# FrontEnd Application using FastAPI #

from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from prometheus_client import Summary, start_http_server, Counter, Gauge, Info
from prometheus_client import disable_created_metrics
import os
from starlette.responses import Response
import asyncio
import uvicorn
from typing import Optional, List
import logging
import httpx

# Creating useful prometheus metrics
# disabling the created metrics
disable_created_metrics()

# _sum will track the total bytes, _count will track the number of calls.
request_size = Summary('input_bytes_fe', 'input data size (bytes)') 
# _sum tracks total time taken, _count tracks number of calls
api_usage = Summary('api_runtime_fe', 'api run time monitoring')

# define the counter to track the usage based on client IP.
api_counter_be = Counter('api_call_counter_be', 'number of times that API is called', ['endpoint', 'client'])
api_counter = Counter('api_call_counter_fe', 'number of times that API is called', ['endpoint', 'client'])
api_gauge = Gauge('api_runtime_secs_fe', 'runtime of the method in seconds', ['endpoint', 'client']) 

# adding build information to the info metric.
info = Info('my_build', 'Prometheus Instrumented AI App for Suicide Detection')
info.info({'version': '0.0.1', 'buildhost': '@Instinct', 'author': 'Joel J @ IITM', 'builddate': 'April 2025'})

# Get the backend URL
#BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:4000")

# Create FastAPI app
app = FastAPI(title="AI Application for Suicide Detection (via text)")
router = APIRouter()

# Mount the static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Models for API
class AnalysisRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    id: int
    message: str
    result: str  
    confidence: float
    timestamp: str
    savedToHistory: bool
    recommendations: Optional[List[str]] = None

# Pydantic model for inputs
class input_data(BaseModel):
    text : str

class input_feedback(BaseModel):
    rating : int
    comments : str

class input_diagnostic(BaseModel):
    text : str
    label : str

# Simulated analyses database
analyses_db = []
current_id = 1

# Setting up the logging 
log_file = "/var/log/frontend.log"
logging.basicConfig(
    level = logging.DEBUG,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("The Backend is starting now !!!")

"""
@app.get("/config")
async def get_config(request:Request):
    return JSONResponse({"backend_base_url" : BACKEND_URL})
"""

# Serve the main HTML page
@app.get("/", response_class=HTMLResponse)
async def get_home(request:Request):
    logging.info("Calling the Dashboard API ")
    api_counter.labels(endpoint = "/main", client=request.client.host).inc()
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/main", response_class=HTMLResponse)
async def get_main(request:Request):
    logging.info("Calling the Dashboard API ")
    api_counter.labels(endpoint = "/main", client=request.client.host).inc()
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Serve the feedback HTML page
@app.get("/feedback", response_class=HTMLResponse)
async def get_feedback(request:Request):
    logging.info("Calling the Dashboard Feedback API ")
    api_counter.labels(endpoint = "/feedback", client=request.client.host).inc()
    with open("feedback.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Serve the diagnostic HTML page
@app.get("/diagnostic", response_class=HTMLResponse)
async def get_diagnostic(request:Request):
    logging.info("Calling the Dashboard Diagnostic API ")
    api_counter.labels(endpoint = "/diagnostic", client=request.client.host).inc()
    with open("diagnostic.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Serve the visualizations HTML page
@app.get("/visualizations", response_class=HTMLResponse)
async def get_visualizations(request:Request):
    logging.info("Calling the Dashboard Visualization API ")
    api_counter.labels(endpoint = "/visualization", client=request.client.host).inc()
    with open("visualizations.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Serve the visualizations HTML page
@app.get("/logs", response_class=HTMLResponse)
async def get_logs(request:Request):
    logging.info("Calling the Dashboard  LogsAPI ")
    api_counter.labels(endpoint = "/logs", client=request.client.host).inc()
    with open("logs.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Serve the contact HTML page
@app.get("/contact", response_class=HTMLResponse)
async def get_contact(request:Request):
    logging.info("Calling the Dashboard contact API ")
    api_counter.labels(endpoint = "/contact", client=request.client.host).inc()
    with open("contact.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

## Calling the Backend from the frontend using docker networks
@router.post("/backend/predict")
async def get_be_predict(input : input_data, request:Request):
    # Logging
    logger.info("Calling backend '/predict' from frontend using docker network")
    # Increasing the counter of API per host
    api_counter_be.labels(endpoint = "/predict", client=request.client.host).inc()
    
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.post(
                "http://backend:4000/predict",
                json=input.dict()
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError:
            logger.error("Backend connection failed")
            raise HTTPException(503, "Backend service unavailable")

@router.post("/backend/feedback")
async def get_be_feedback(input: input_feedback, request: Request):
    # Logging
    logger.info("Calling backend '/feedback' from frontend using docker network")
    
    # Increasing the counter of API per host
    api_counter_be.labels(endpoint="/feedback", client=request.client.host).inc()
    
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.post(
                "http://backend:4000/feedback",
                json=input.dict()  # Correct: send input data as JSON
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError:
            logger.error("Backend connection failed")
            raise HTTPException(503, "Backend service unavailable")

@router.post("/backend/diagnostic")
async def get_be_diagnostic(input: input_diagnostic, request: Request):
    # Logging
    logger.info("Calling backend '/diagnostic' from frontend using docker network")
    
    # Increasing the counter of API per host
    api_counter_be.labels(endpoint="/diagnostic", client=request.client.host).inc()
    
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.post(
                "http://backend:4000/diagnostic",
                json=input.dict()  # Convert input model to dict for JSON payload
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError:
            logger.error("Backend connection failed")
            raise HTTPException(503, "Backend service unavailable")

@router.get("/backend/visualizations/{plot_name}")
async def get_be_visualizations(plot_name: str, request: Request):
    # Logging
    logger.info("Calling backend '/visualizations' from frontend using docker network")

    # Increasing the counter of API per host
    api_counter_be.labels(endpoint="/visualizations", client=request.client.host).inc()

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(f"http://backend:4000/visualizations/{plot_name}")

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except httpx.ConnectError:
            logger.error("Backend connection failed")
            raise HTTPException(503, "Backend service unavailable")

@router.get("/backend/logs/{container_name}")
async def get_be_logs(container_name: str, request: Request):
    # Logging
    logger.info("Calling backend '/logs' from frontend using docker network")

    # Increasing the counter of API per host
    api_counter_be.labels(endpoint="/logs", client=request.client.host).inc()

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(f"http://backend:4000/logs/{container_name}")

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except httpx.ConnectError:
            logger.error("Backend connection failed")
            raise HTTPException(503, "Backend service unavailable")

app.include_router(router)

# Get recent analyses
@app.get("/api/history")
async def get_history():
    # Return only saved analyses, newest first
    return [a for a in analyses_db if a["savedToHistory"]]

# Save analysis to history
@app.post("/api/history/{analysis_id}")
async def save_to_history(analysis_id: int):
    for analysis in analyses_db:
        if analysis["id"] == analysis_id:
            analysis["savedToHistory"] = True
            return {"success": True}
    
    raise HTTPException(status_code=404, detail="Analysis not found")

# Serve the static files
@app.get("/styles.css")
async def get_css():
    return FileResponse("styles.css")

@app.get("/script.js")
async def get_js():
    return FileResponse("script.js")

# Run the server directly when script is executed
if __name__ == "__main__":
    # Starting to expose the metrics at prometheus monitor
    logger.info("Starting the prometheus monitor at port 18002")
    start_http_server(18002)

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("__main__:app", host="0.0.0.0", port=port)