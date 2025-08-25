# MaiAgent Docker 服務啟動與設定指南

## 服務清單與對外埠口
- **django**: 8000
- **celeryworker**: 無對外埠
- **celerybeat**: 無對外埠
- **flower**: 5555
- **postgres**: 5432（僅 compose 網路內）
- **redis**: 6379（僅 compose 網路內）
- **elasticsearch**: 9200
- **node（開發用）**: 3000

## 設定檔與環境變數
- `src/maiagent/docker-compose.local.yml`: 本地服務編排與健康檢查
- `src/maiagent/.envs/.local/.django`
  - 建議設定：
    - `DATABASE_URL=postgres://debug:debug@postgres:5432/maiagent`
    - `REDIS_URL=redis://redis:6379/0`
- `src/maiagent/.envs/.local/.postgres`
  - `POSTGRES_HOST=postgres`
  - `POSTGRES_PORT=5432`
  - `POSTGRES_DB=maiagent`
  - `POSTGRES_USER=debug`
  - `POSTGRES_PASSWORD=debug`
- `src/maiagent/.envs/.local/.elasticsearch`
  - `ELASTICSEARCH_URL=http://elasticsearch:9200`
  - `ELASTICSEARCH_VERIFY_SSL=false`

> 變更 `.envs` 後，請重建對應服務讓變數生效（見下）。

## 啟動/停止（整體）
於 Windows PowerShell，從 `D:\project\maiagent\src\maiagent` 執行：

```powershell
# 啟動基礎依賴（DB/Cache/ES）
docker compose -f docker-compose.local.yml up -d postgres redis elasticsearch

# 啟動應用與任務服務
docker compose -f docker-compose.local.yml up -d django celeryworker celerybeat flower

# 查看狀態
docker compose -f docker-compose.local.yml ps

# 停止全部
docker compose -f docker-compose.local.yml down
```

## 單一服務操作
```powershell
# 啟動/重啟/停止
docker compose -f docker-compose.local.yml up -d django
docker compose -f docker-compose.local.yml restart django
docker compose -f docker-compose.local.yml stop django

# 變更 env 後重建（不動相依）
docker compose -f docker-compose.local.yml up -d --force-recreate --no-deps django

# 觀看日誌
docker compose -f docker-compose.local.yml logs -f django
```

## 健康檢查與驗證
```powershell
# 檢查服務健康
docker compose -f docker-compose.local.yml ps

# 驗證 Elasticsearch
Invoke-WebRequest http://localhost:9200 -UseBasicParsing | Select-Object -Expand Content

# 驗證 Django（管理後台）
Invoke-WebRequest http://localhost:8000/admin/login/ -UseBasicParsing | Select-Object -Expand StatusCode
```

## 建立超級使用者
- 互動式：
```powershell
docker exec -it maiagent_local_django python manage.py createsuperuser
```
- 無互動：
```powershell
docker exec -it maiagent_local_django /bin/bash -lc "DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=admin python manage.py createsuperuser --noinput"
```

## 常見問題與建議
- 變更 `.envs/.local/*.env` 後無效：請重建相應容器（例如 `--force-recreate --no-deps django`）。
- Elasticsearch 記憶體：Docker Desktop 建議至少 2GB 分配。
- PowerShell 指令串接：Windows PowerShell 不支援 `&&`，請用分號或逐行執行。

## 常用服務網址
- Django Admin: `http://localhost:8000/admin/login/`
- Flower: `http://localhost:5555/`
- Elasticsearch: `http://localhost:9200/`
