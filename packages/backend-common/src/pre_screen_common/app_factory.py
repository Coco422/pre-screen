from fastapi import FastAPI


def create_service_app(service_name: str) -> FastAPI:
    app = FastAPI(title=f"pre-screen-{service_name}")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"service": service_name, "status": "ok"}

    return app
