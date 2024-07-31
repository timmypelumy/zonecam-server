from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import get_settings
from app.routes.users import router as users_router
from app.tasks.setup import huey

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
    expose_headers=["WWW-Authenticate"],

)


@app.get("/")
async def status(req: Request):

    return {
        "app_name": settings.app_name,
        "app_url": settings.app_url,
        "debug": settings.debug,
        "message": "Welcome to SecureBloc API",
        "ip_address": req.client.host,
    }


app.include_router(users_router, prefix="/api")
