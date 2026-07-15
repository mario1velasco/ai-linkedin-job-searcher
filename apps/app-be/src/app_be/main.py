"""FastAPI application entrypoint."""

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app_be.services import linkedin_service
from app_be.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI()
app.state.linkedin_access_token = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_methods=["GET", "POST"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/greetings/{name}")
def read_greetings(name: str):
    return {"message": f"Hello, {name}!"}


# ****** EJEMPL ENDPOINTS PARA VALIDAR DATOS DE ENTRADA Y SALIDA CON PYDANTIC ******
# ! Pydantic. Se hace para validar los datos de entrada y salida. Se puede usar para validar la entrada de datos en un endpoint.
class UserData(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    age: int = Field(ge=0, le=120)


user_database: dict[int, UserData] = {}  # Simulated in-memory database


@app.post("/user/{user_id}")
# ! user_id es un path parameter, user_data es un body parameter
def update_user(user_id: int, user_data: UserData):
    """Update user data."""
    user = user_database.get(user_id)
    if user is None:
        logger.info("Creating new user with ID %d", user_id)
    else:
        logger.info("Updating existing user with ID %d", user_id)
    user_database[user_id] = user_data
    return {
        "message": "User data updated successfully",
        "user_id": user_id,
        "user_data": user_data.model_dump(),
    }


# ****** EJEMPL ENDPOINTS PARA VALIDAR DATOS DE ENTRADA Y SALIDA CON PYDANTIC ******

# ***** EJEMPLO DE ENDPOINTS PARA OAUTH CON LINKEDIN ******
# * 1. Iniciar el flujo de OAuth con LinkedIn. Endpoint: /linkedin/login
# * 2. Una vez que el usuario autoriza la aplicación, LinkedIn redirige al endpoint de callback con un código de autorización.
# * 3. El endpoint de callback intercambia el código de autorización por un token de acceso.


@app.get("/linkedin/login")
def linkedin_login():
    """Initiate the LinkedIn OAuth flow and retrieve an access token."""
    logger.info("Initiating LinkedIn OAuth login flow")
    linkedin_service.login()
    return {"message": "LinkedIn login initiated. Please check your browser."}


@app.get("/callback")
def callback(code: str, state: str):
    """Handle the OAuth callback and exchange the code for an access token."""
    logger.info("Received OAuth callback (state=%s)", state)
    try:
        app.state.linkedin_access_token = linkedin_service.handle_oauth_callback(
            code, state
        )
    except ValueError:
        logger.warning("OAuth callback rejected: state mismatch (state=%s)", state)
        raise
    except requests.HTTPError:
        logger.exception("Failed to exchange OAuth code for an access token")
        raise
    logger.info("LinkedIn access token acquired successfully")
    return {"message": "Callback received. You can close this window."}


# ***** EJEMPLOS DE ENDPOINTS PARA OAUTH CON LINKEDIN ******


@app.get("/linkedin/userinfo")
def get_linkedin_userinfo():
    if not app.state.linkedin_access_token:
        logger.warning("Userinfo requested but no LinkedIn access token is set")
        raise HTTPException(status_code=401, detail="Not authenticated with LinkedIn.")
    return linkedin_service.get_userinfo(app.state.linkedin_access_token)


@app.get("/linkedin/jobs")
def search_linkedin_jobs(
    keywords: str = "Angular",
    geo_id: str = "105646813",
    distance: float = 0.0,
    hours: int = 24,
    remote: bool = True,
    salary_bucket: str | None = None,
):

    try:
        jobs = linkedin_service.search_jobs(
            keywords=keywords,
            geo_id=geo_id,
            distance=distance,
            hours=hours,
            remote=remote,
            salary_bucket=salary_bucket,
        )
    except RuntimeError as error:
        logger.error("LinkedIn job search failed: %s", error)
        raise HTTPException(status_code=502, detail=str(error)) from error

    return jobs
