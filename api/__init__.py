# API package
from .app import app
from .internal import router as internal_router
app.include_router(internal_router, prefix="/_internal")
