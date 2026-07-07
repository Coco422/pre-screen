from services.resume.app.domain.models import ResumeBatchResult, ResumeParseResult, ResumeUpload


class ResumeRepository:
    def __init__(self) -> None:
        self._uploads: dict[str, ResumeUpload] = {}
        self._parse_results: dict[str, ResumeParseResult] = {}
        self._batches: dict[str, ResumeBatchResult] = {}

    def reset(self) -> None:
        self._uploads.clear()
        self._parse_results.clear()
        self._batches.clear()

    def save_upload(self, upload: ResumeUpload) -> ResumeUpload:
        self._uploads[upload.upload_id] = upload
        return upload

    def get_upload(self, upload_id: str) -> ResumeUpload | None:
        return self._uploads.get(upload_id)

    def list_uploads(self) -> tuple[ResumeUpload, ...]:
        return tuple(self._uploads.values())

    def save_parse_result(self, result: ResumeParseResult) -> ResumeParseResult:
        self._parse_results[result.file_id] = result
        return result

    def get_parse_result(self, file_id: str) -> ResumeParseResult | None:
        return self._parse_results.get(file_id)

    def list_parse_results(self) -> tuple[ResumeParseResult, ...]:
        return tuple(self._parse_results.values())

    def save_batch_result(self, result: ResumeBatchResult) -> ResumeBatchResult:
        self._batches[result.batch_id] = result
        return result

    def get_batch_result(self, batch_id: str) -> ResumeBatchResult | None:
        return self._batches.get(batch_id)

    def latest_batch_result(self) -> ResumeBatchResult | None:
        if not self._batches:
            return None
        return max(self._batches.values(), key=lambda item: item.created_at)


resume_repository = ResumeRepository()
