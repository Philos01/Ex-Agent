
"""
Skills API - Endpoints for skill management and execution
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["skills"])


class SkillExecuteRequest(BaseModel):
    """Request model for skill execution"""
    skill_name: str
    parameters: Dict[str, Any] = {}


class SkillResponse(BaseModel):
    """Standard skill response model"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    formatted_result: Optional[str] = None


@router.get("/skills", summary="List all available skills")
async def list_skills():
    """
    Get a list of all discovered and available skills with their metadata.
    
    Returns:
        List of skill metadata including name and description
    """
    try:
        from app.skills.skill_manager import get_skill_manager
        skill_manager = get_skill_manager()
        skills = skill_manager.list_skills()
        return {
            "success": True,
            "count": len(skills),
            "skills": skills
        }
    except Exception as e:
        logger.error(f"Failed to list skills: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills/{skill_name}/metadata", summary="Get skill metadata")
async def get_skill_metadata(skill_name: str):
    """
    Get Level 1 metadata for a specific skill.
    
    Args:
        skill_name: Name of the skill
        
    Returns:
        Skill metadata (name and description)
    """
    try:
        from app.skills.skill_manager import get_skill_manager
        skill_manager = get_skill_manager()
        metadata = skill_manager.get_skill_metadata(skill_name)
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Skill not found: {skill_name}")
        
        return {
            "success": True,
            "skill_name": skill_name,
            "metadata": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata for skill {skill_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills/{skill_name}/instructions", summary="Get skill instructions")
async def get_skill_instructions(skill_name: str):
    """
    Get Level 2 full instructions from SKILL.md.
    
    Args:
        skill_name: Name of the skill
        
    Returns:
        Full SKILL.md content if available
    """
    try:
        from app.skills.skill_manager import get_skill_manager
        skill_manager = get_skill_manager()
        instructions = skill_manager.get_skill_instructions(skill_name)
        
        return {
            "success": True,
            "skill_name": skill_name,
            "has_instructions": instructions is not None,
            "instructions": instructions
        }
    except Exception as e:
        logger.error(f"Failed to get instructions for skill {skill_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills/{skill_name}/resources", summary="List skill resources")
async def list_skill_resources(skill_name: str):
    """
    Get Level 3 resource list for a skill.
    
    Args:
        skill_name: Name of the skill
        
    Returns:
        List of resource paths available for the skill
    """
    try:
        from app.skills.skill_manager import get_skill_manager
        skill_manager = get_skill_manager()
        resources = skill_manager.get_skill_resources(skill_name)
        
        return {
            "success": True,
            "skill_name": skill_name,
            "count": len(resources),
            "resources": resources
        }
    except Exception as e:
        logger.error(f"Failed to list resources for skill {skill_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills/execute", summary="Execute a skill")
async def execute_skill(request: SkillExecuteRequest):
    """
    Execute a skill with the given parameters.
    
    Args:
        request: Skill execution request containing skill name and parameters
        
    Returns:
        Skill execution result, including formatted output for LLM consumption
    """
    try:
        from app.skills.skill_manager import get_skill_manager
        skill_manager = get_skill_manager()
        
        logger.info(f"Executing skill: {request.skill_name} with params: {request.parameters}")
        
        result = skill_manager.execute_skill(request.skill_name, **request.parameters)
        formatted_result = skill_manager.format_skill_result(result)
        
        response = SkillResponse(
            success=result.get("success", False),
            data=result if result.get("success") else None,
            error=result.get("error") if not result.get("success") else None,
            formatted_result=formatted_result
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to execute skill {request.skill_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills/auto-execute", summary="Auto-detect and execute skill based on question")
async def auto_execute_skill(question: str):
    """
    Automatically detect if a skill should be used for the given question,
    and execute it if appropriate.
    
    Args:
        question: User's question to analyze
        
    Returns:
        Skill execution result if a skill was triggered, or indication that no skill matched
    """
    try:
        from app.skills.skill_manager import get_skill_manager
        skill_manager = get_skill_manager()
        
        should_use, skill_name, params = skill_manager.should_use_skill(question)
        
        if not should_use:
            return {
                "success": True,
                "skill_triggered": False,
                "message": "No skill matched the question"
            }
        
        logger.info(f"Auto-executing skill: {skill_name} with params: {params}")
        
        result = skill_manager.execute_skill(skill_name, **params)
        formatted_result = skill_manager.format_skill_result(result)
        
        return {
            "success": True,
            "skill_triggered": True,
            "skill_name": skill_name,
            "parameters": params,
            "result": result,
            "formatted_result": formatted_result
        }
        
    except Exception as e:
        logger.error(f"Failed in auto-execute for question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

