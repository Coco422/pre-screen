from pre_screen_common.app_factory import create_service_app
from services.judge_bridge.app.api.submissions import router as submissions_router

app = create_service_app("judge-bridge")
app.include_router(submissions_router)
