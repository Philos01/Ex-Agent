"""
Skills API - Endpoints for skill management and execution - v1
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["skills"])


class SkillExecuteRequest(BaseModel):
    skill_name: str
    parameters: Dict[str, Any] = {}


class SkillResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    formatted_result: Optional[str] = None


@router.get("", summary="List all available skills")
async def list_skills():
    try:
        from app.skills import get_skill_manager
        skill_manager = get_skill_manager()
        skills = skill_manager.list_skills()
        return {
            "success": True,
            "count": len(skills),
            "skills": skills
        }
    except Exception as e:
        logger.error("Failed to list skills: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_name}/metadata", summary="Get skill metadata")
async def get_skill_metadata(skill_name: str):
    try:
        from app.skills import get_skill_manager
        skill_manager = get_skill_manager()
        skills = skill_manager.list_skills()
        skill_info = next((s for s in skills if s["name"] == skill_name), None)

        if not skill_info:
            raise HTTPException(status_code=404, detail=f"Skill not found: {skill_name}")

        return {
            "success": True,
            "skill_name": skill_name,
            "metadata": {"name": skill_info["name"], "description": skill_info["description"]}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get metadata for skill %s: %s", skill_name, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_name}/instructions", summary="Get skill instructions")
async def get_skill_instructions(skill_name: str):
    try:
        from app.skills.skill_manager import get_skill_manager
        from pathlib import Path
        skill_manager = get_skill_manager()
        skills = skill_manager.list_skills()
        skill_info = next((s for s in skills if s["name"] == skill_name), None)

        instructions = None
        if skill_info:
            project_root = Path(__file__).parent.parent.parent.parent.parent
            skill_dir = project_root / "skills" / skill_name
            skill_md_path = skill_dir / "SKILL.md"
            if skill_md_path.exists():
                try:
                    with open(skill_md_path, 'r', encoding='utf-8') as f:
                        instructions = f.read()
                except Exception:
                    pass

        if instructions is None:
            try:
                from app.skills.skill_manager import get_skill_manager
                legacy_manager = get_skill_manager()
                instructions = legacy_manager.get_skill_instructions(skill_name)
            except Exception:
                pass

        return {
            "success": True,
            "skill_name": skill_name,
            "has_instructions": instructions is not None,
            "instructions": instructions
        }
    except Exception as e:
        logger.error("Failed to get instructions for skill %s: %s", skill_name, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_name}/resources", summary="List skill resources")
async def list_skill_resources(skill_name: str):
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
        logger.error("Failed to list resources for skill %s: %s", skill_name, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", summary="Execute a skill")
async def execute_skill(request: SkillExecuteRequest):
    try:
        from app.skills import get_skill_manager
        skill_manager = get_skill_manager()

        logger.info("Executing skill: %s with params: %s", request.skill_name, request.parameters)

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
        logger.error("Failed to execute skill %s: %s", request.skill_name, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-execute", summary="Auto-detect and execute skill based on question")
async def auto_execute_skill(question: str):
    try:
        from app.skills import get_skill_manager
        skill_manager = get_skill_manager()

        should_use, skill_name, params = skill_manager.should_use_skill(question)

        if not should_use:
            return {
                "success": True,
                "skill_triggered": False,
                "message": "No skill matched the question"
            }

        logger.info("Auto-executing skill: %s with params: %s", skill_name, params)

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
        logger.error("Failed in auto-execute for question: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
