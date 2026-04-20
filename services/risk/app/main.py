from pre_screen_common.app_factory import create_service_app
from services.risk.app.api.events import router as events_router

app = create_service_app("risk")
app.include_router(events_router)
