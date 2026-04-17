# OpenAI API 凭证安全管理方案

## 概述

本文档详细说明了为 OpenAI API 凭证实施的最高级别安全保护措施，确保凭证既不允许被未授权访问，也不允许以任何形式持久化存储。

## 一、安全架构设计

### 1.1 凭证管理方式

**完全移除持久化存储**
- API 密钥不再保存到 `config.json` 文件
- API 密钥仅通过环境变量注入
- 配置文件仅存储非敏感配置项

**环境变量配置**
```bash
# 在项目根目录创建 .env 文件
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
```

## 二、安全措施详解

### 2.1 环境变量注入（要求 1）

**实施细节**
- 使用 `python-dotenv` 库加载环境变量
- 环境变量在应用启动时加载到内存
- 凭证仅在运行时存在于内存中
- 不写入任何磁盘文件

**验证方法**
```python
# 检查 config.json 中不包含 API 密钥
import json
with open('config.json', 'r') as f:
    config = json.load(f)
assert 'openai_api_key' not in config
```

### 2.2 权限控制机制（要求 2）

**管理员权限验证**
- 配置修改仅允许管理员用户
- 使用 `get_current_user` 依赖进行身份验证
- 角色检查：`current_user.role.lower() == "admin"`

**代码位置**
- `backend/app/api/routes.py:367-419` - 配置端点权限控制
- `backend/app/api/auth.py` - 认证和用户管理

### 2.3 审计日志系统（要求 4）

**已实施的审计日志**
1. **API 密钥访问日志**
   - 记录每次 API 密钥访问
   - 跟踪访问计数和最后访问时间
   - 异常访问模式检测（>100 次访问触发警告）
   - 位置：`backend/app/core/config.py:164-181`

2. **配置变更审计**
   - 记录所有配置修改
   - 包含变更前后值
   - 记录操作用户、IP 地址、User Agent
   - 位置：`backend/app/api/routes.py:377-419`
   - 审计模型：`backend/app/models/audit_log.py`
   - 审计服务：`backend/app/services/audit.py`

**审计日志格式**
```
[AUDIT] username - config_change - system_config:provider
[SECURITY] 2026-04-17 10:30:00 - INFO - API key accessed - Total accesses: 42, Last access: 2026-04-17T10:30:00.123456
```

### 2.4 实时监控（要求 5）

**异常访问检测**
- API 密钥访问计数监控
- 高访问量自动告警（>100 次）
- 安全日志实时输出到控制台

**扩展建议**
生产环境可考虑集成：
- Prometheus + Grafana 监控
- ELK (Elasticsearch + Logstash + Kibana) 日志分析
- 第三方安全监控服务

### 2.5 禁止持久化存储（要求 6）

**多层防护机制**
1. **配置加载时过滤** - `load_config()` 自动移除 API 密钥
2. **配置保存时过滤** - `save_config()` 自动移除 API 密钥
3. **API 响应过滤** - `/config` 端点从不返回 API 密钥
4. **默认配置不含密钥** - `DEFAULT_CONFIG` 不包含 API 密钥

**代码位置**
- `backend/app/core/config.py:118-161`

### 2.6 开发环境安全（要求 7）

**开发环境安全措施**
- `.env.example` 提供配置模板
- `.gitignore` 严格保护敏感文件
- 开发文档明确说明安全要求
- 前端 UI 提示正确配置方式

## 三、配置步骤

### 3.1 环境变量配置

1. **复制配置模板**
```bash
cp .env.example .env
```

2. **编辑 .env 文件**
```env
OPENAI_API_KEY=sk-your-actual-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
SECRET_KEY=your-strong-secret-key-here
```

3. **验证文件权限**
```bash
# 确保 .env 文件仅所有者可读写
chmod 600 .env  # Linux/Mac
# Windows: 通过文件资源管理器设置权限
```

### 3.2 后端依赖安装

确认 `python-dotenv` 已包含在 `requirements.txt` 中：
```
python-dotenv>=1.0.0
```

### 3.3 重启服务

修改 `.env` 文件后必须重启后端服务：
```bash
# 停止当前服务 (Ctrl+C)
# 重新启动
cd backend
python -m uvicorn app.main:app --reload
```

## 四、验证方法

### 4.1 安全检查清单

- [ ] `config.json` 中不包含 `openai_api_key`
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] API 密钥仅从环境变量加载
- [ ] `/config` 端点不返回 API 密钥
- [ ] 配置修改需要管理员权限
- [ ] 配置变更有审计日志
- [ ] API 密钥访问有安全日志

### 4.2 自动化验证测试

```python
# test_security.py
import json
from app.core.config import load_config, get_complete_config

def test_no_api_key_in_saved_config():
    """验证 API 密钥不被持久化"""
    cfg = load_config()
    assert 'openai_api_key' not in cfg
    
def test_api_key_from_env():
    """验证 API 密钥从环境变量加载"""
    cfg = get_complete_config()
    # 仅在环境变量已设置时测试
    import os
    if os.getenv('OPENAI_API_KEY'):
        assert 'openai_api_key' in cfg
```

## 五、安全最佳实践

### 5.1 凭证轮换策略（要求 3）

**建议的轮换周期**
- 生产环境：不超过 90 天
- 开发环境：不超过 30 天
- 密钥泄露后：立即轮换

**轮换步骤**
1. 在 OpenAI 控制台生成新 API 密钥
2. 更新 `.env` 文件中的 `OPENAI_API_KEY`
3. 重启后端服务
4. 验证服务正常运行
5. 在 OpenAI 控制台吊销旧密钥

### 5.2 最小权限原则

- 使用专门的服务账号
- 仅授予必要的 API 权限
- 定期审计权限配置
- 及时移除不必要的访问权限

### 5.3 监控和告警

**关键监控指标**
- API 密钥访问频率
- 异常时间访问（深夜、周末）
- 异常 IP 地址访问
- API 调用量突变

**告警渠道**
- 邮件告警
- 短信/电话告警（严重事件）
- 即时通讯工具（Slack、钉钉等）

## 六、安全应急响应预案（要求 8）

### 6.1 泄露识别

**可能的泄露迹象**
- 异常的 API 调用量
- 未知来源的 API 访问
- 安全日志中的可疑活动
- 收到 OpenAI 的异常使用告警

### 6.2 应急处理流程

**步骤 1：立即停用泄露的密钥**
```bash
# 1. 访问 OpenAI 控制台
# 2. 导航到 API Keys 页面
# 3. 找到泄露的密钥并点击 "Revoke"
```

**步骤 2：生成新密钥**
```bash
# 1. 在 OpenAI 控制台生成新 API 密钥
# 2. 更新本地 .env 文件
OPENAI_API_KEY=sk-new-secure-key-here
```

**步骤 3：重启服务**
```bash
# 重启后端服务以加载新密钥
```

**步骤 4：调查泄露原因**
- 检查版本控制历史
- 审查访问日志
- 检查服务器安全
- 识别泄露点并修复

**步骤 5：审计影响**
- 检查异常 API 调用
- 评估数据泄露范围
- 通知相关受影响方（如适用）

### 6.3 事后改进

1. **根本原因分析** - 确定泄露的根本原因
2. **修复安全漏洞** - 修复导致泄露的问题
3. **更新安全策略** - 根据经验改进安全措施
4. **加强培训** - 对团队进行安全意识培训
5. **定期演练** - 定期进行应急响应演练

## 七、相关文件位置

| 组件 | 文件路径 |
|------|----------|
| 配置管理 | `backend/app/core/config.py` |
| API 路由 | `backend/app/api/routes.py` |
| 审计日志模型 | `backend/app/models/audit_log.py` |
| 审计服务 | `backend/app/services/audit.py` |
| 认证模块 | `backend/app/api/auth.py` |
| 前端设置页 | `frontend/src/views/SettingsView.vue` |
| 环境变量模板 | `.env.example` |
| Git 忽略配置 | `.gitignore` |

## 八、联系与支持

如有安全问题或疑虑，请立即联系系统管理员或安全团队。

---

**文档版本**: 1.0  
**最后更新**: 2026-04-17  
**安全级别**: 🔴 最高级别
