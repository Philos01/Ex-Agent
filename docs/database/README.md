# 数据库设计文档

## 目录
- [数据库架构](#数据库架构)
- [ER 图](#er-图)
- [数据表设计](#数据表设计)
- [索引设计](#索引设计)
- [数据迁移](#数据迁移)
- [备份与恢复](#备份与恢复)
- [常见问题](#常见问题)

---

## 数据库架构

### 数据库选型

项目使用 **SQLite** 作为主要数据库，具有以下优势：

| 特性 | 说明 |
|------|------|
| 类型 | 轻量级嵌入式关系型数据库 |
| 部署 | 无需单独的数据库服务器 |
| 存储 | 单文件存储（`data/lab_agent.db`） |
| 并发 | 支持读写并发（有一定限制） |
| 适用场景 | 中小规模应用、开发环境 |

**注意**: 生产环境建议使用 PostgreSQL 或 MySQL 替代 SQLite，以获得更好的并发性能和可靠性。

### ORM 框架

使用 **SQLAlchemy 2.0** 作为 ORM 框架：

```python
# backend/app/core/config.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

---

## ER 图

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│    users     │         │   sessions   │         │   messages   │
├──────────────┤         ├──────────────┤         ├──────────────┤
│ id (PK)      │◄────────│ id (PK)      │◄────────│ id (PK)      │
│ username     │ 1      *│ user_id (FK) │ 1      *│ session_id(FK)│
│ email        │         │ session_name │         │ user_id (FK) │
│ password_hash│         │ is_active    │         │ role         │
│ role         │         │ last_msg_... │         │ content      │
│ is_active    │         │ message_count│         │ sources (JSON)│
│ created_at   │         │ created_at   │         │ created_at   │
│ updated_at   │         │ updated_at   │         │ updated_at   │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │
       │ 1                      │ 1
       │ *                      │ *
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│  documents   │         │  audit_logs  │
├──────────────┤         ├──────────────┤
│ id (PK)      │         │ id (PK)      │
│ user_id (FK) │         │ user_id (FK) │
│ filename     │         │ action       │
│ file_path    │         │ details (JSON)│
│ file_size    │         │ ip_address   │
│ file_type    │         │ user_agent   │
│ created_at   │         │ created_at   │
│ updated_at   │         └──────────────┘
└──────────────┘

┌──────────────┐         ┌──────────────┐
│ permissions  │         │role_permissio│
├──────────────┤         │     ns       │
│ id (PK)      │         ├──────────────┤
│ name         │◄────────│ id (PK)      │
│ code         │   *    *│ role_id (FK) │
│ description  │         │ permission_id│
│ created_at   │         │ (FK)         │
│ updated_at   │         │ created_at   │
└──────────────┘         └──────────────┘
```

---

## 数据表设计

### 1. BaseModel（基础模型）

所有数据表都继承自 `BaseModel`，包含公共字段：

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | PK, AI | 主键，自增 |
| version_id | Integer | NOT NULL, DEFAULT 0 | 乐观锁版本号 |
| created_at | DateTime | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | NOT NULL, DEFAULT NOW(), ON UPDATE NOW() | 更新时间 |

### 2. users（用户表）

存储用户账户信息。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | PK, AI | 用户 ID |
| username | String(50) | UNIQUE, NOT NULL, INDEX | 用户名 |
| email | String(100) | UNIQUE, NOT NULL, INDEX | 邮箱 |
| password_hash | String(128) | NOT NULL | 密码哈希值（bcrypt） |
| role | String(20) | NOT NULL, DEFAULT 'user', INDEX | 用户角色：user/admin |
| is_active | Boolean | NOT NULL, DEFAULT TRUE, INDEX | 是否激活 |
| version_id | Integer | NOT NULL, DEFAULT 0 | 乐观锁版本号 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**关系**：
- 1 对多：sessions（一个用户可以有多个会话）
- 1 对多：messages（一个用户可以有多个消息）
- 1 对多：documents（一个用户可以上传多个文档）

**索引**：
- PRIMARY KEY (id)
- UNIQUE INDEX (username)
- UNIQUE INDEX (email)
- INDEX (role)
- INDEX (is_active)

### 3. sessions（会话表）

存储聊天会话信息。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | PK, AI | 会话 ID |
| user_id | Integer | FK, NOT NULL, INDEX | 用户 ID（关联 users 表） |
| session_name | String(100) | NOT NULL | 会话名称 |
| is_active | Boolean | NOT NULL, DEFAULT TRUE, INDEX | 是否活跃 |
| last_message_preview | Text | NULLABLE | 最后一条消息预览 |
| message_count | Integer | NOT NULL, DEFAULT 0 | 消息总数 |
| version_id | Integer | NOT NULL, DEFAULT 0 | 乐观锁版本号 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**关系**：
- 多对 1：user（多个会话属于一个用户）
- 1 对多：messages（一个会话包含多条消息）

**索引**：
- PRIMARY KEY (id)
- INDEX (user_id)
- INDEX (is_active)
- FOREIGN KEY (user_id) REFERENCES users(id)

### 4. messages（消息表）

存储聊天消息内容。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | PK, AI | 消息 ID |
| session_id | Integer | FK, NOT NULL, INDEX | 会话 ID（关联 sessions 表） |
| user_id | Integer | FK, NOT NULL, INDEX | 用户 ID（关联 users 表） |
| role | String(20) | NOT NULL, INDEX | 角色：user/assistant/system |
| content | Text | NOT NULL | 消息内容 |
| sources | JSON | NULLABLE | 引用来源（JSON 格式） |
| version_id | Integer | NOT NULL, DEFAULT 0 | 乐观锁版本号 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**关系**：
- 多对 1：session（多条消息属于一个会话）
- 多对 1：user（多条消息属于一个用户）

**索引**：
- PRIMARY KEY (id)
- INDEX (session_id)
- INDEX (user_id)
- INDEX (role)
- FOREIGN KEY (session_id) REFERENCES sessions(id)
- FOREIGN KEY (user_id) REFERENCES users(id)

### 5. documents（文档表）

存储上传的文档信息。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | PK, AI | 文档 ID |
| user_id | Integer | FK, NOT NULL, INDEX | 用户 ID（关联 users 表） |
| filename | String(255) | NOT NULL, INDEX | 文件名 |
| file_path | String(500) | NOT NULL | 文件存储路径 |
| file_size | BigInteger | NOT NULL | 文件大小（字节） |
| file_type | String(50) | NOT NULL | 文件类型（扩展名） |
| version_id | Integer | NOT NULL, DEFAULT 0 | 乐观锁版本号 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**关系**：
- 多对 1：user（多个文档属于一个用户）

**索引**：
- PRIMARY KEY (id)
- INDEX (user_id)
- INDEX (filename)
- FOREIGN KEY (user_id) REFERENCES users(id)

### 6. audit_logs（审计日志表）

记录用户操作审计日志。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | PK, AI | 日志 ID |
| user_id | Integer | FK, NULLABLE, INDEX | 用户 ID（关联 users 表） |
| action | String(100) | NOT NULL, INDEX | 操作类型 |
| details | JSON | NULLABLE | 详细信息（JSON 格式） |
| ip_address | String(50) | NULLABLE | IP 地址 |
| user_agent | String(500) | NULLABLE | 用户代理 |
| version_id | Integer | NOT NULL, DEFAULT 0 | 乐观锁版本号 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**关系**：
- 多对 1：user（多条日志属于一个用户）

**索引**：
- PRIMARY KEY (id)
- INDEX (user_id)
- INDEX (action)
- INDEX (created_at)
- FOREIGN KEY (user_id) REFERENCES users(id)

### 7. permissions（权限表）

存储系统权限定义。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | PK, AI | 权限 ID |
| name | String(100) | NOT NULL, INDEX | 权限名称 |
| code | String(100) | UNIQUE, NOT NULL, INDEX | 权限代码 |
| description | Text | NULLABLE | 权限描述 |
| version_id | Integer | NOT NULL, DEFAULT 0 | 乐观锁版本号 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**关系**：
- 多对多：通过 role_permissions 关联角色

**索引**：
- PRIMARY KEY (id)
- UNIQUE INDEX (code)
- INDEX (name)

### 8. role_permissions（角色权限关联表）

存储角色与权限的多对多关系。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | PK, AI | 关联 ID |
| role_id | Integer | NOT NULL, INDEX | 角色 ID |
| permission_id | Integer | FK, NOT NULL, INDEX | 权限 ID（关联 permissions 表） |
| version_id | Integer | NOT NULL, DEFAULT 0 | 乐观锁版本号 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**关系**：
- 多对 1：permission（多个关联指向一个权限）

**索引**：
- PRIMARY KEY (id)
- INDEX (role_id)
- INDEX (permission_id)
- UNIQUE INDEX (role_id, permission_id)
- FOREIGN KEY (permission_id) REFERENCES permissions(id)

---

## 索引设计

### 已创建索引

| 表名 | 索引名 | 字段 | 类型 | 用途 |
|------|--------|------|------|------|
| users | PRIMARY | id | 主键 | 唯一标识 |
| users | ix_users_username | username | 唯一 | 用户登录 |
| users | ix_users_email | email | 唯一 | 用户登录/找回密码 |
| users | ix_users_role | role | 普通 | 角色筛选 |
| users | ix_users_is_active | is_active | 普通 | 活跃用户筛选 |
| sessions | PRIMARY | id | 主键 | 唯一标识 |
| sessions | ix_sessions_user_id | user_id | 普通 | 用户会话查询 |
| sessions | ix_sessions_is_active | is_active | 普通 | 活跃会话筛选 |
| messages | PRIMARY | id | 主键 | 唯一标识 |
| messages | ix_messages_session_id | session_id | 普通 | 会话消息查询 |
| messages | ix_messages_user_id | user_id | 普通 | 用户消息查询 |
| messages | ix_messages_role | role | 普通 | 角色筛选 |
| documents | PRIMARY | id | 主键 | 唯一标识 |
| documents | ix_documents_user_id | user_id | 普通 | 用户文档查询 |
| documents | ix_documents_filename | filename | 普通 | 文件名搜索 |
| audit_logs | PRIMARY | id | 主键 | 唯一标识 |
| audit_logs | ix_audit_logs_user_id | user_id | 普通 | 用户日志查询 |
| audit_logs | ix_audit_logs_action | action | 普通 | 操作类型筛选 |
| audit_logs | ix_audit_logs_created_at | created_at | 普通 | 时间范围查询 |
| permissions | PRIMARY | id | 主键 | 唯一标识 |
| permissions | ix_permissions_code | code | 唯一 | 权限代码查询 |
| permissions | ix_permissions_name | name | 普通 | 权限名称搜索 |
| role_permissions | PRIMARY | id | 主键 | 唯一标识 |
| role_permissions | ix_role_permissions_role_id | role_id | 普通 | 角色权限查询 |
| role_permissions | ix_role_permissions_permission_id | permission_id | 普通 | 权限角色查询 |

### 索引使用建议

1. **查询优化**：
   - 优先使用带索引的字段进行查询
   - 避免在索引字段上使用函数运算

2. **写入性能**：
   - 索引会降低写入性能，只在必要时创建
   - 定期分析索引使用情况，删除无用索引

---

## 数据迁移

### 初始化数据库

```bash
cd backend/scripts
python init_db.py create
```

### 删除所有表（谨慎使用）

```bash
cd backend/scripts
python init_db.py drop
```

### 迁移脚本

项目使用 `migrate_db.py` 进行数据库迁移：

```bash
cd backend/scripts
python migrate_db.py
```

### 手动迁移步骤

1. 备份现有数据库
2. 创建新的数据库结构
3. 迁移数据
4. 验证数据完整性
5. 切换到新数据库

---

## 备份与恢复

### 备份数据库

```bash
# 方法 1：直接复制数据库文件
cp data/lab_agent.db data/lab_agent.db.backup

# 方法 2：使用 SQLite 命令行
sqlite3 data/lab_agent.db ".backup 'data/lab_agent.db.backup'"
```

### 恢复数据库

```bash
# 方法 1：直接复制备份文件
cp data/lab_agent.db.backup data/lab_agent.db

# 方法 2：使用 SQLite 命令行
sqlite3 data/lab_agent.db ".restore 'data/lab_agent.db.backup'"
```

### 定时备份建议

创建定时任务（如 cron job）定期备份：

```bash
# 每天凌晨 2 点备份
0 2 * * * cp /path/to/data/lab_agent.db /path/to/backups/lab_agent_$(date +\%Y\%m\%d).db
```

---

## 常见问题

### 1. 数据库锁定错误

**症状**: `database is locked` 错误

**解决方案**:
1. 确保没有其他进程正在访问数据库
2. 增加超时时间：
   ```python
   engine = create_engine(
       DATABASE_URL,
       connect_args={"check_same_thread": False, "timeout": 30}
   )
   ```
3. 使用连接池（SQLite 支持有限）

### 2. 数据库文件损坏

**症状**: 无法读取数据库，报错 `database disk image is malformed`

**解决方案**:
1. 尝试恢复：
   ```bash
   sqlite3 data/lab_agent.db ".recover" | sqlite3 data/lab_agent_recovered.db
   ```
2. 从备份恢复
3. 重新初始化数据库

### 3. 性能问题

**症状**: 查询速度慢

**解决方案**:
1. 检查索引是否正确使用
2. 使用 `EXPLAIN QUERY PLAN` 分析查询
3. 考虑使用更快的数据库（如 PostgreSQL）
4. 优化查询语句

### 4. 外键约束错误

**症状**: 删除或更新时违反外键约束

**解决方案**:
1. 检查关联数据是否存在
2. 使用级联删除（已在模型中配置）
3. 先删除子记录，再删除父记录

### 5. 生产环境数据库选择

**建议**: 生产环境推荐使用 PostgreSQL

SQLite 不适合高并发写入的生产环境。建议迁移到 PostgreSQL：

```python
# 修改 DATABASE_URL
DATABASE_URL=postgresql://user:password@localhost:5432/lab_agent
```

---

## 下一步

- 查看 [后端开发文档](../backend/README.md) 了解如何使用数据库
- 查看 [API 接口文档](../api/README.md) 了解数据操作接口