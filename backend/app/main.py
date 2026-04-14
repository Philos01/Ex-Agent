from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.api import auth
from app.api import sessions
from app.api import skills
from app.core.rate_limit import login_limiter, api_limiter

app = FastAPI(title="实验室智能助手 - 后端")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Apply stricter limit for login endpoint
    if "/api/auth/login" in request.url.path:
        await login_limiter(request)
    else:
        await api_limiter(request)
    
    response = await call_next(request)
    return response

# Include routers
app.include_router(routes.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(skills.router, prefix="/api")

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "实验室智能助手 - 后端 API", "version": "2.0"}
