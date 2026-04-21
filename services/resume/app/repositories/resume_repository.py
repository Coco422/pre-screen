from services.resume.app.domain.models import ResumeUpload


class ResumeRepository:
    def __init__(self) -> None:
        self._uploads: dict[str, ResumeUpload] = {}

    def reset(self) -> None:
        self._uploads.clear()

    def save_upload(self, upload: ResumeUpload) -> ResumeUpload:
        self._uploads[upload.upload_id] = upload
        return upload

    def list_uploads(self) -> tuple[ResumeUpload, ...]:
        return tuple(self._uploads.values())


resume_repository = ResumeRepository()
