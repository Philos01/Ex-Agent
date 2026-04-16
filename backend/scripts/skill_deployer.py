
#!/usr/bin/env python3
"""
ClawHub Skill Deployer - 一键部署 ClawHub 技能包到 Agent 系统
"""
import argparse
import os
import sys
import yaml
import json
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Any


class ClawHubSkillDeployer:
    """ClawHub 技能部署器
    
    功能特性:
    - 支持 ClawHub 技能包格式 (SKILL.md + _meta.json)
    - 自动解析技能元数据
    - 完整复制技能包内容
    - 自动生成 Python 技能实现
    - 更新配置文件
    - 部署验证
    """
    
    def __init__(self, project_root=None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.skills_dir = self.project_root / "skills"
        self.backend_dir = self.project_root / "backend"
        self.config_path = self.project_root / "skills_config.yaml"
        self.skills_py_dir = self.backend_dir / "app" / "skills"
        
        self.skills_dir.mkdir(exist_ok=True)
        self.skills_py_dir.mkdir(exist_ok=True)
    
    def parse_skill_md_frontmatter(self, skill_md_path):
        """解析 SKILL.md 的 YAML frontmatter"""
        if not skill_md_path.exists():
            return None
        
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            return None
        
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            return frontmatter if isinstance(frontmatter, dict) else None
        except yaml.YAMLError:
            return None
    
    def parse_meta_json(self, meta_path):
        """解析 _meta.json 文件"""
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    
    def validate_skill_package(self, package_path):
        """验证 ClawHub 技能包是否有效"""
        print("[1/6] 验证技能包...")
        
        if not package_path.exists():
            return False, "技能包路径不存在: " + str(package_path), None
        
        if not package_path.is_dir():
            return False, "技能包必须是一个目录: " + str(package_path), None
        
        skill_md = package_path / "SKILL.md"
        if not skill_md.exists():
            return False, "技能包缺少 SKILL.md 文件", None
        
        print("  [OK] SKILL.md 已找到")
        
        frontmatter = self.parse_skill_md_frontmatter(skill_md)
        if not frontmatter:
            print("  [WARN] SKILL.md 缺少或格式错误的 YAML frontmatter")
        
        meta_json = package_path / "_meta.json"
        meta_data = None
        if meta_json.exists():
            meta_data = self.parse_meta_json(meta_json)
            if meta_data:
                print("  [OK] _meta.json 已解析: " + str(meta_data.get('slug', 'unknown')) + " v" + str(meta_data.get('version', 'unknown')))
        
        skill_name = None
        if frontmatter and 'name' in frontmatter:
            skill_name = frontmatter['name']
        elif meta_data and 'slug' in meta_data:
            skill_name = meta_data['slug']
        else:
            skill_name = package_path.name
        
        print("  [OK] 技能名称: " + skill_name)
        print("  OK: 技能包验证通过")
        return True, skill_name, {'frontmatter': frontmatter, 'meta': meta_data}
    
    def copy_skill_package(self, package_path, skill_name):
        """复制技能包到项目 skills 目录"""
        print("\n[2/6] 复制技能包...")
        
        target_dir = self.skills_dir / skill_name
        
        # if target_dir.exists():
        #     print("  [WARN] 技能目录已存在，正在备份: " + str(target_dir))
        #     backup_dir = self.skills_dir / (skill_name + ".backup")
        #     if backup_dir.exists():
        #         shutil.rmtree(backup_dir)
        #     shutil.move(target_dir, backup_dir)
        #     print("  [OK] 已备份到: " + str(backup_dir))
        
        shutil.copytree(package_path, target_dir)
        print("  [OK] 技能包已复制到: " + str(target_dir))
        return True
    
    def generate_skill_implementation(self, skill_name, skill_info):
        """生成 Python 技能实现文件（已弃用 - 新系统不需要）"""
        print("\n[3/6] 技能实现生成（新系统已不需要）...")
        print("  [INFO] 新技能系统不需要生成 Python 实现文件，跳过此步骤")
        return True
    
    def _to_camel_case(self, snake_str):
        """将 kebab-case 或 snake_case 转换为 CamelCase"""
        parts = re.split(r'[-_]', snake_str)
        return ''.join(part.capitalize() for part in parts)
    
    def update_configuration(self, skill_name, skill_info, custom_config=None):
        """更新 skills_config.yaml"""
        print("\n[4/6] 更新配置...")
        
        if not self.config_path.exists():
            config_data = {"global": {"enabled": True, "auto_discover": True}}
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        
        meta = skill_info.get('meta', {})
        skill_config = {
            "enabled": True,
            "version": meta.get('version', '1.0.0')
        }
        
        if custom_config:
            skill_config.update(custom_config)
        
        config_data[skill_name] = skill_config
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print("  [OK] 配置已更新: " + skill_name)
        return True
    
    def verify_deployment(self, skill_name):
        """验证部署是否成功"""
        print("\n[5/6] 验证部署...")
        
        skill_dir = self.skills_dir / skill_name
        
        checks = [
            ("技能目录", skill_dir.exists()),
            ("SKILL.md", (skill_dir / "SKILL.md").exists()),
            ("配置文件", self.config_path.exists())
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "[OK]" if passed else "[FAIL]"
            print("  " + status + " " + name)
            if not passed:
                all_passed = False
        
        return all_passed
    
    def deploy(self, package_path, custom_config=None):
        """完整的部署流程"""
        package_path = Path(package_path)
        
        print("=" * 70)
        print("ClawHub 技能部署器")
        print("=" * 70)
        
        is_valid, skill_name, skill_info = self.validate_skill_package(package_path)
        if not is_valid:
            print("\nERROR: " + skill_name)
            return False
        
        success = True
        
        if success and not self.copy_skill_package(package_path, skill_name):
            success = False
        
        if success and not self.generate_skill_implementation(skill_name, skill_info):
            success = False
        
        if success and not self.update_configuration(skill_name, skill_info, custom_config):
            success = False
        
        if success and not self.verify_deployment(skill_name):
            success = False
        
        print("\n[6/6] 完成!")
        if success:
            print("\n" + "=" * 70)
            print("部署成功!")
            print("=" * 70)
            print("\n技能名称: " + skill_name)
            print("安装位置: " + str(self.skills_dir / skill_name))
            print("\n下一步:")
            print("  1. 重启后端服务以加载新技能")
            print("  2. 通过 API 测试技能是否正常工作")
            print("  3. 编辑 " + str(self.config_path) + " 配置技能参数")
        else:
            print("\nERROR: 部署失败")
        
        return success
    
    def list_skills(self):
        """列出已安装的技能"""
        print("=" * 70)
        print("已安装的技能")
        print("=" * 70)
        
        if not self.skills_dir.exists():
            print("\n没有找到已安装的技能")
            return
        
        skills = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
        
        print("\n共 " + str(len(skills)) + " 个技能:")
        for skill in sorted(skills):
            print("  - " + skill)
        
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            print("\n技能配置 (" + self.config_path.name + "):")
            for skill_name, skill_config in config.items():
                if skill_name != "global":
                    enabled = "启用" if skill_config.get("enabled", True) else "禁用"
                    version = skill_config.get("version", "unknown")
                    print("  - " + skill_name + ": " + enabled + " (v" + version + ")")
    
    def show_info(self, package_path):
        """显示技能包信息"""
        package_path = Path(package_path)
        
        print("=" * 70)
        print("技能包信息")
        print("=" * 70)
        print("\n路径: " + str(package_path))
        
        is_valid, skill_name, skill_info = self.validate_skill_package(package_path)
        if not is_valid:
            print("\n错误: " + skill_name)
            return
        
        print("\n技能名称: " + skill_name)
        
        frontmatter = skill_info.get('frontmatter', {})
        if frontmatter:
            print("\nSKILL.md Frontmatter:")
            for key, value in frontmatter.items():
                print("  " + key + ": " + str(value))
        
        meta = skill_info.get('meta', {})
        if meta:
            print("\n_meta.json:")
            for key, value in meta.items():
                print("  " + key + ": " + str(value))
        
        print("\n技能包内容:")
        self._list_package_contents(package_path, indent="  ")
    
    def _list_package_contents(self, path, indent=""):
        """递归列出技能包内容"""
        for item in sorted(path.iterdir()):
            if item.name.startswith('.'):
                continue
            print(indent + item.name + ("/" if item.is_dir() else ""))
            if item.is_dir():
                self._list_package_contents(item, indent + "  ")


def main():
    parser = argparse.ArgumentParser(
        description="ClawHub 技能部署器 - 一键部署 ClawHub 技能包到 Agent 系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 部署本地技能包
  python skill_deployer.py deploy ../arxiv-watcher-1.0.0
  
  # 部署并自定义配置
  python skill_deployer.py deploy ../arxiv-watcher-1.0.0 --config '{"enabled": true}'
  
  # 查看技能包信息
  python skill_deployer.py info ../arxiv-watcher-1.0.0
  
  # 列出已安装的技能
  python skill_deployer.py list
        """
    )
    
    subparsers = parser.add_subparsers(title="命令", dest="command")
    
    # 部署命令
    deploy_parser = subparsers.add_parser("deploy", help="部署技能包")
    deploy_parser.add_argument("package_path", help="技能包目录路径")
    deploy_parser.add_argument("--config", help="JSON 格式的自定义配置")
    
    # 信息命令
    info_parser = subparsers.add_parser("info", help="查看技能包信息")
    info_parser.add_argument("package_path", help="技能包目录路径")
    
    # 列表命令
    list_parser = subparsers.add_parser("list", help="列出已安装的技能")
    
    args = parser.parse_args()
    
    deployer = ClawHubSkillDeployer()
    
    if args.command == "deploy":
        custom_config = None
        if args.config:
            try:
                custom_config = json.loads(args.config)
            except json.JSONDecodeError as e:
                print("ERROR: 配置 JSON 格式错误: " + str(e))
                sys.exit(1)
        
        success = deployer.deploy(args.package_path, custom_config)
        sys.exit(0 if success else 1)
    
    elif args.command == "info":
        deployer.show_info(args.package_path)
    
    elif args.command == "list":
        deployer.list_skills()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

