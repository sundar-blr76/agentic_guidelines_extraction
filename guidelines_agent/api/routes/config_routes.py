"""Configuration and system info API routes (/config/*)."""
from fastapi import APIRouter
from guidelines_agent.api.schemas.common_schemas import SuccessResponse
from guidelines_agent.core.config import Config
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=SuccessResponse)
async def get_system_config():
    """Get system configuration and environment information."""
    try:
        config_info = Config.get_environment_info()
        
        return SuccessResponse(
            success=True,
            data=config_info,
            message="System configuration retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting system config: {e}", exc_info=True)
        return SuccessResponse(
            success=False,
            message=f"Error retrieving system configuration: {str(e)}"
        )