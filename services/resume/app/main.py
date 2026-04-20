from pre_screen_common.app_factory import create_service_app
from services.resume.app.api.profiles import router as profiles_router
from services.resume.app.api.uploads import router as uploads_router

app = create_service_app("resume")
app.include_router(uploads_router)
app.include_router(profiles_router)
