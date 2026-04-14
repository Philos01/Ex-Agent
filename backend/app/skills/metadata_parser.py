
"""
Skill Metadata Parser - Parse YAML frontmatter from skill packages
"""
import yaml
import re
from pathlib import Path
from typing import Dict, Any


def parse_skill_frontmatter(skill_md_path):
    """
    Parse YAML frontmatter from SKILL.md file
    
    Args:
        skill_md_path: Path to SKILL.md file
        
    Returns:
        Dictionary with name and description
    """
    if not skill_md_path.exists():
        raise FileNotFoundError("SKILL.md not found: {}".format(skill_md_path))
    
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match YAML frontmatter (content between --- separators)
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    
    if not frontmatter_match:
        raise ValueError("No YAML frontmatter found in {}".format(skill_md_path))
    
    frontmatter_content = frontmatter_match.group(1)
    
    try:
        metadata = yaml.safe_load(frontmatter_content)
    except yaml.YAMLError as e:
        raise ValueError("Failed to parse YAML frontmatter: {}".format(e))
    
    # Ensure required fields exist
    if "name" not in metadata:
        raise ValueError("Missing required field: 'name' in YAML frontmatter")
    if "description" not in metadata:
        raise ValueError("Missing required field: 'description' in YAML frontmatter")
    
    return metadata


def get_skill_metadata(skill_dir):
    """
    Get metadata from skill package directory
    
    Args:
        skill_dir: Skill package directory path (e.g., skills/arxiv-watcher)
        
    Returns:
        Skill metadata dictionary
    """
    skill_md_path = skill_dir / "SKILL.md"
    return parse_skill_frontmatter(skill_md_path)

