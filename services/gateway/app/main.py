from pre_screen_common.app_factory import create_service_app
from services.gateway.app.api.admin import router as admin_router
from services.gateway.app.api.public_exam import router as public_exam_router

app = create_service_app("gateway")
app.include_router(admin_router)
app.include_router(public_exam_router)
