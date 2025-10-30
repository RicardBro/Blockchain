# API package
from .app import app
from .internal import router as internal_router
from .jobs import router as jobs_router

app.include_router(internal_router, prefix="/_internal")
app.include_router(jobs_router, prefix="/jobs")
