#!/usr/bin/env python3
"""
ArXiv Search Script - Python version
Cross-platform alternative to shell script
"""
import argparse
import json
import sys
import requests
import xml.etree.ElementTree as ET


def parse_arxiv_xml(xml_content):
    """
    Parse ArXiv XML response and extract paper information
    
    Args:
        xml_content: XML string from ArXiv API
        
    Returns:
        List of paper dictionaries
    """
    papers = []
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    
    try:
        root = ET.fromstring(xml_content)
        entries = root.findall('.//atom:entry', namespaces)
        
        for entry in entries:
            paper = {}
            
            # Title
            title_elem = entry.find('atom:title', namespaces)
            paper['title'] = title_elem.text.strip() if title_elem is not None else ''
            
            # Summary/Abstract
            summary_elem = entry.find('atom:summary', namespaces)
            paper['summary'] = summary_elem.text.strip() if summary_elem is not None else ''
            
            # Published date
            published_elem = entry.find('atom:published', namespaces)
            paper['published'] = published_elem.text if published_elem is not None else ''
            
            # Authors
            author_elems = entry.findall('atom:author/atom:name', namespaces)
            paper['authors'] = [a.text for a in author_elems if a.text]
            
            # Categories
            category_elems = entry.findall('atom:category', namespaces)
            paper['categories'] = [c.get('term', '') for c in category_elems]
            
            # Links
            links = entry.findall('atom:link', namespaces)
            paper['abs_url'] = ''
            paper['pdf_url'] = ''
            
            for link in links:
                rel = link.get('rel', '')
                href = link.get('href', '')
                title = link.get('title', '')
                
                if rel == 'alternate' and not paper['abs_url']:
                    paper['abs_url'] = href
                elif title == 'pdf':
                    paper['pdf_url'] = href
            
            papers.append(paper)
            
    except Exception as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
    
    return papers


def main():
    parser = argparse.ArgumentParser(description="ArXiv Search")
    parser.add_argument("--params", help="JSON parameter file path")
    args = parser.parse_args()
    
    # 先尝试读取 skill_config.json 配置
    default_count = 5
    try:
        import os
        from pathlib import Path
        script_dir = Path(__file__).parent
        config_path = script_dir.parent / "skill_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_count = config.get("default_count", 5)
    except Exception:
        pass
    
    query = "all"
    count = default_count
    
    # 处理 --params 参数
    if args.params:
        try:
            with open(args.params, 'r', encoding='utf-8') as f:
                params = json.load(f)
            query = params.get("query", "all")
            count = params.get("count", default_count)
        except Exception as e:
            print(f"错误: 无法读取参数文件: {e}", file=sys.stderr)
            sys.exit(1)
    
    # 构建查询 URL
    base_url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": count,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        # 解析 XML 并提取论文信息
        papers = parse_arxiv_xml(response.text)
        
        # 返回成功结果
        result = {
            "success": True,
            "data": {
                "papers": papers,
                "query": query,
                "count": len(papers)
            }
        }
        print(json.dumps(result, ensure_ascii=True))
        
    except requests.exceptions.RequestException as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result, ensure_ascii=True))
        sys.exit(1)


if __name__ == "__main__":
    main()
