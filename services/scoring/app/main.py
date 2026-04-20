from pre_screen_common.app_factory import create_service_app
from services.scoring.app.api.reviews import router as reviews_router

app = create_service_app("scoring")
app.include_router(reviews_router)
