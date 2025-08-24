# MaiAgent GenAI 自動回覆平台

> 以 Django 為核心，結合 Celery、PostgreSQL、Elasticsearch 與 LangChain 的企業級對話系統。支援場景化配置、權限管控、非同步生成與全文檢索，協助團隊在安全可控的環境下快速導入 LLM 能力。

## 系統架構

![系統架構圖](../../doc/design/System_Architecture.png)

## 核心組件簡介

- **Server（Django）**：提供 RESTful API 與 Web 入口，負責接收使用者訊息、寫入資料庫並觸發 Celery 任務，亦提供會話列表與全文檢索查詢功能。參考 `doc/design/RESTful_API_Design.md`。
- **PostgreSQL**：主要關聯式資料庫，儲存使用者/群組/角色與權限、場景設定、會話與訊息、任務狀態等結構化資料，透過索引與外鍵維持一致性。參考 `doc/design/Database_Design.md`。
- **Elasticsearch**：會話與訊息的全文檢索引擎，採用 IK 中文分詞，支援依角色/群組的權限邊界查詢與高亮顯示。參考 `doc/design/Elasticsearch_Fields_design.md`。
- **Celery**：非同步任務佇列，處理 LLM 生成與長耗時工作；具備 TLS 加密的 Broker、連線池與退避重試等穩定性機制。參考 `doc/design/Celery_Design.md`。
- **LangChain（LLMs）**：封裝場景化對話流程與 RAG/Prompt 設定，依場景配置產生 AI 回覆並回寫結果；同時提供場景列表與設定能力。概要見 `doc/design/System_Architecture.md`。
- **操作與權限模型**：以「一人一角色、一公司一群組」為邊界，對應全文檢索、場景管理與對話等操作的授權規則。參考 `doc/design/Operations_and_Permissions_Mapping.md`。

---

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## 開發與測試（框架預設）

### 建立超級使用者

```bash
python manage.py createsuperuser
```

### 型別與測試

```bash
mypy maiagent
pytest
coverage run -m pytest && coverage html
```

### 啟動 Celery（本機）

```bash
celery -A config.celery_app worker -l info
celery -A config.celery_app beat
```

更多框架預設說明可參考 Cookiecutter Django 官方文件。
