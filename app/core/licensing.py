"""License validation — re-export from cloud-backed module."""

from app.core.license_cloud import (
    dev_key_result,
    invalidate_license_cache,
    is_dev_key,
    supporter_plan_status,
    supporter_unlock_active,
    validate_license,
)

__all__ = [
    'dev_key_result',
    'invalidate_license_cache',
    'is_dev_key',
    'supporter_plan_status',
    'supporter_unlock_active',
    'validate_license',
]

# Legacy aliases used by older tests / tooling
dev_keys_enabled = lambda: True  # noqa: E731
is_dev_license_key = is_dev_key
