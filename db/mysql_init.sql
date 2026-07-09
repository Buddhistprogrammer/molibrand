-- ============================================================
-- MySQL 8.0 业务数据表结构
-- 参考 Architecture.md 6.1 / 7.4 / 8.3
-- ============================================================

SET NAMES utf8mb4;

-- ---------- 用户 ----------
CREATE TABLE IF NOT EXISTS users (
    id            BIGINT PRIMARY KEY AUTO_INCREMENT,
    phone         VARCHAR(32)  NOT NULL UNIQUE,
    nickname      VARCHAR(64),
    password_hash VARCHAR(255) NOT NULL,
    -- user=普通用户 / reviewer=审核咨询师 / admin=管理员
    role          ENUM('user','reviewer','admin') NOT NULL DEFAULT 'user',
    -- 订阅套餐（PRD 9.1）
    plan          ENUM('none','single','monthly','annual') NOT NULL DEFAULT 'none',
    quota_left    INT NOT NULL DEFAULT 0,      -- 剩余诊断次数
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- 知识库文档（元数据；正文向量在 pgvector） ----------
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    title       VARCHAR(255) NOT NULL,
    content     LONGTEXT     NOT NULL,
    doc_type    ENUM('methodology','case','template','faq') NOT NULL,
    tags        JSON,
    source_url  VARCHAR(512),                 -- 原始文件 OSS 地址
    status      ENUM('pending','chunked','indexed','error') NOT NULL DEFAULT 'pending',
    chunk_count INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    doc_id      BIGINT NOT NULL,
    chunk_index INT    NOT NULL,
    content     TEXT   NOT NULL,
    token_count INT,
    pgvector_id BIGINT,                        -- 对应 pgvector knowledge_embeddings.id
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    INDEX idx_doc (doc_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- 咨询会话 ----------
CREATE TABLE IF NOT EXISTS consultations (
    id         BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id    BIGINT NOT NULL,
    title      VARCHAR(255),
    status     ENUM('active','reporting','reviewing','completed','closed') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- 对话消息 ----------
CREATE TABLE IF NOT EXISTS chat_messages (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    consultation_id BIGINT NOT NULL,
    role            ENUM('user','assistant','system') NOT NULL,
    content         TEXT   NOT NULL,
    content_type    ENUM('text','image','audio','video','mixed') NOT NULL DEFAULT 'text',
    attachments     JSON,                      -- [{type,url}]
    token_count     INT,
    rag_chunks      JSON,                      -- 命中的知识库 chunk id 列表
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id) ON DELETE CASCADE,
    INDEX idx_consultation (consultation_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- 诊断报告 + 人工审核 ----------
CREATE TABLE IF NOT EXISTS diagnostic_reports (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    consultation_id BIGINT NOT NULL,
    user_id         BIGINT NOT NULL,
    content         JSON   NOT NULL,           -- 结构化报告
    status          ENUM('draft','pending_review','approved','rejected','delivered') NOT NULL DEFAULT 'draft',
    reviewer_id     BIGINT,
    review_comment  TEXT,
    reviewed_at     TIMESTAMP NULL,
    delivered_at    TIMESTAMP NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- 审计日志 ----------
CREATE TABLE IF NOT EXISTS audit_logs (
    id         BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id    BIGINT,
    action     VARCHAR(64) NOT NULL,
    target     VARCHAR(128),
    detail     JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_action (user_id, action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------- 种子数据：默认管理员/审核员（密码见 README，务必上线前修改） ----------
-- 密码 hash 对应明文 "admin123"（bcrypt），仅供本地开发
INSERT INTO users (phone, nickname, password_hash, role, plan, quota_left)
VALUES ('13800000000', '茉莉总', '$2b$12$e0MYzXyjpJS7Pd0RVvHwHe1Hpq5cQ2q5oQ9r0bkYq6oQZ6oQZ6oQ', 'admin', 'annual', 999)
ON DUPLICATE KEY UPDATE phone = phone;
