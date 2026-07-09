"""OSS 上传：签发 STS 临时凭证供前端直传（架构 8.2）。

未配置 OSS/STS 时返回占位凭证，前端可走本地 mock 上传流程。
"""
import json
import time

from app.config import settings

# 各文件类型的 OSS 路径与大小限制（架构 8.2.2）
_PATH_RULES = {
    "image": "consultation/{uid}/images/{ts}_{name}",
    "audio": "consultation/{uid}/audio/{ts}_{name}",
    "video": "consultation/{uid}/videos/{ts}_{name}",
    "document": "knowledge/{ts}_{name}",
}


def build_object_key(file_type: str, filename: str, user_id: int) -> str:
    rule = _PATH_RULES.get(file_type, _PATH_RULES["document"])
    return rule.format(uid=user_id, ts=int(time.time()), name=filename)


def issue_sts(file_type: str, filename: str, user_id: int) -> dict:
    """签发 OSS 临时上传凭证。"""
    object_key = build_object_key(file_type, filename, user_id)

    if not (settings.oss_access_key_id and settings.sts_role_arn):
        # 降级：返回占位，提示前端 OSS 未配置
        return {
            "access_key_id": "MOCK",
            "access_key_secret": "MOCK",
            "security_token": "MOCK",
            "endpoint": settings.oss_endpoint or "mock-endpoint",
            "bucket": settings.oss_bucket or "mock-bucket",
            "object_key": object_key,
            "expiration": "mock",
        }

    # 延迟导入，避免未装 SDK 时影响启动
    from alibabacloud_sts20150401.client import Client as StsClient
    from alibabacloud_sts20150401 import models as sts_models
    from alibabacloud_tea_openapi import models as open_api_models

    policy = {
        "Version": "1",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["oss:PutObject"],
                "Resource": [f"acs:oss:*:*:{settings.oss_bucket}/{object_key}"],
            }
        ],
    }
    config = open_api_models.Config(
        access_key_id=settings.oss_access_key_id,
        access_key_secret=settings.oss_access_key_secret,
        endpoint=f"sts.{settings.oss_region}.aliyuncs.com",
    )
    client = StsClient(config)
    resp = client.assume_role(
        sts_models.AssumeRoleRequest(
            role_arn=settings.sts_role_arn,
            role_session_name="upload",
            policy=json.dumps(policy),
            duration_seconds=settings.sts_duration_seconds,
        )
    )
    cred = resp.body.credentials
    return {
        "access_key_id": cred.access_key_id,
        "access_key_secret": cred.access_key_secret,
        "security_token": cred.security_token,
        "endpoint": settings.oss_endpoint,
        "bucket": settings.oss_bucket,
        "object_key": object_key,
        "expiration": cred.expiration,
    }
