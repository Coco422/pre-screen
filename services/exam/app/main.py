from services.exam.app.api.answers import router as answers_router
from services.exam.app.api.invitations import router as invitations_router
from pre_screen_common.app_factory import create_service_app
from services.exam.app.api.papers import router as papers_router
from services.exam.app.api.sessions import router as sessions_router
from services.exam.app.api.templates import router as templates_router

app = create_service_app("exam")
app.include_router(invitations_router)
app.include_router(sessions_router)
app.include_router(answers_router)
app.include_router(templates_router)
app.include_router(papers_router)
