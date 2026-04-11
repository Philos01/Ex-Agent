
# SQLite 数据库迁移指南

本指南详细说明如何将项目数据库从 PostgreSQL 迁移到 SQLite。

## 目录

1. [为什么选择 SQLite](#为什么选择-sqlite)
2. [迁移概览](#迁移概览)
3. [已完成的修改](#已完成的修改)
4. [初始化数据库](#初始化数据库)
5. [测试验证](#测试验证)
6. [常见问题](#常见问题)

---

## 为什么选择 SQLite

### 优势

1. **零配置**：无需安装数据库服务器，开箱即用
2. **轻量级**：单个文件存储，便于备份和迁移
3. **跨平台**：Windows、Linux、macOS 完全兼容
4. **ACID 兼容**：支持事务，数据安全性有保障
5. **足够性能**：对于中小型应用完全够用

### 适用场景

- 单用户或小团队使用
- 开发和测试环境
- 需要便携性的应用
- 并发写入较少的场景

---

## 迁移概览

### 修改的文件

1. **`backend/app/core/config.py`**
   - 修改数据库连接字符串为 SQLite 格式
   - 添加 `check_same_thread=False` 配置
   - 移除 PostgreSQL 特有的连接池配置

2. **`backend/app/models/base.py`**
   - 移除 `DateTime(timezone=True)`，因为 SQLite 不支持时区
   - 使用普通 `DateTime` 类型

3. **`backend/init_db.py`**
   - 保持原样，SQLAlchemy 抽象层自动处理差异

---

## 已完成的修改

### 1. 数据库连接配置 (`config.py`)

**修改前 (PostgreSQL)**:
```python
DATABASE_URL = "postgresql://postgres:password@localhost:5433/Ex-Agent"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False
)
```

**修改后 (SQLite)**:
```python
DB_PATH = DATA_DIR / "lab_agent.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
```

### 2. 基础模型 (`base.py`)

**修改前**:
```python
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

**修改后**:
```python
created_at = Column(DateTime, server_default=func.now(), nullable=False)
updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

---

## 初始化数据库

### 步骤 1: 确保数据目录存在

数据库文件会自动创建在 `data/lab_agent.db`，确保 `data` 目录存在。

### 步骤 2: 创建数据库表

运行初始化脚本：

```bash
cd backend
python init_db.py create
```

**预期输出**:
```
Creating database tables...
[OK] All tables created successfully!

Created tables:
  - users
  - permissions
  - role_permissions
  - sessions
  - messages
  - documents
```

### 步骤 3: 验证数据库文件

检查 `data` 目录下是否生成了 `lab_agent.db` 文件：

```bash
ls -lh data/
```

应该能看到类似：
```
-rw-r--r--  1 user  group    20K Apr 11 10:00 lab_agent.db
```

---

## 测试验证

### 1. 基础功能测试

启动后端服务：

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 数据库操作验证

#### 测试 1: 检查 API 健康

访问 `http://localhost:8000/`，应该看到：

```json
{
  "message": "实验室智能助手 - 后端 API",
  "version": "2.0"
}
```

#### 测试 2: 验证用户认证

尝试注册和登录用户，确保数据库操作正常。

#### 测试 3: 验证会话管理

创建会话、发送消息，确保数据正确保存。

#### 测试 4: 验证文档上传

上传文档，确保文档信息正确保存。

---

## 数据库表结构

### 1. users (用户表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | VARCHAR(50) | 用户名（唯一） |
| email | VARCHAR(100) | 邮箱（唯一） |
| password_hash | VARCHAR(128) | 密码哈希 |
| role | VARCHAR(20) | 用户角色 |
| is_active | BOOLEAN | 是否激活 |
| version_id | INTEGER | 乐观锁版本号 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 2. sessions (会话表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户ID（外键） |
| session_name | VARCHAR(100) | 会话名称 |
| is_active | BOOLEAN | 是否活跃 |
| last_message_preview | TEXT | 最后消息预览 |
| message_count | INTEGER | 消息总数 |
| version_id | INTEGER | 乐观锁版本号 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3. messages (消息表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| session_id | INTEGER | 会话ID（外键） |
| user_id | INTEGER | 用户ID（外键） |
| role | VARCHAR(20) | 角色 |
| content | TEXT | 消息内容 |
| sources | JSON | 引用来源 |
| version_id | INTEGER | 乐观锁版本号 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 4. documents (文档表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户ID（外键） |
| filename | VARCHAR(255) | 文件名 |
| file_path | VARCHAR(500) | 文件路径 |
| file_size | BIGINT | 文件大小（字节） |
| file_type | VARCHAR(50) | 文件类型 |
| version_id | INTEGER | 乐观锁版本号 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 5. permissions (权限表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(50) | 权限名称（唯一） |
| description | TEXT | 权限描述 |
| version_id | INTEGER | 乐观锁版本号 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 6. role_permissions (角色权限关联表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| role | VARCHAR(20) | 角色名称 |
| permission_id | INTEGER | 权限ID（外键） |
| version_id | INTEGER | 乐观锁版本号 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

## 常见问题

### Q1: SQLite 和 PostgreSQL 数据类型有什么区别？

**A**: 主要区别：

| PostgreSQL | SQLite | 说明 |
|-----------|--------|------|
| TIMESTAMP WITH TIME ZONE | DATETIME | SQLite 不支持时区 |
| BIGSERIAL | INTEGER AUTOINCREMENT | 自增字段 |
| VARCHAR(n) | VARCHAR(n) 或 TEXT | SQLite 会自动处理 |
| JSONB | JSON | SQLite 支持 JSON 类型 |

### Q2: 如何备份 SQLite 数据库？

**A**: 只需复制数据库文件：

```bash
# 备份
cp data/lab_agent.db data/lab_agent.db.backup

# 恢复
cp data/lab_agent.db.backup data/lab_agent.db
```

### Q3: 如何查看 SQLite 数据库内容？

**A**: 使用 SQLite 命令行工具：

```bash
# 进入数据库
sqlite3 data/lab_agent.db

# 查看所有表
.tables

# 查询用户
SELECT * FROM users;

# 退出
.quit
```

或者使用图形化工具：
- **DB Browser for SQLite** (跨平台)
- **DBeaver** (跨平台)
- **DataGrip** (JetBrains)

### Q4: SQLite 支持并发吗？

**A**: 
- SQLite 支持**并发读**
- SQLite 使用**数据库级锁**处理写操作
- 对于本项目的使用场景完全足够
- 如果需要高并发写入，可考虑其他数据库

### Q5: 如何从 SQLite 迁移回 PostgreSQL？

**A**: 
1. 使用 SQLAlchemy 导出数据
2. 或使用 `sqlite3` 工具导出为 SQL
3. 在 PostgreSQL 中导入

### Q6: 数据库文件太大怎么办？

**A**: 
```sql
-- 清理数据库
VACUUM;

-- 或者在命令行
sqlite3 data/lab_agent.db "VACUUM;"
```

---

## 性能优化建议

### 1. 定期维护

```sql
-- 重建数据库文件，优化性能
VACUUM;
```

### 2. 索引优化

当前模型已包含必要的索引，SQLite 会自动优化查询。

### 3. 连接配置

我们已配置 `check_same_thread=False`，这是 FastAPI 多线程环境的推荐配置。

---

## 总结

SQLite 迁移已完成！主要改动：

1. ✅ 修改数据库连接配置为 SQLite
2. ✅ 调整数据模型适配 SQLite
3. ✅ 保留完整的数据库功能
4. ✅ 提供详细的迁移和使用指南

现在可以开始使用 SQLite 数据库了！🎉
