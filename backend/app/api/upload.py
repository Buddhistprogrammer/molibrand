"""文件上传：签发 OSS STS 临时凭证（前端直传，架构 8.2）。"""
from fastapi import APIRouter

from app.core import CurrentUser
from app.schemas import STSRequest, STSResponse
from app.services import oss

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/sts", response_model=STSResponse)
async def get_upload_sts(body: STSRequest, user: CurrentUser):
    cred = oss.issue_sts(body.file_type, body.filename, user.id)
    return STSResponse(**cred)
