# Deep News OAI 배포 가이드

## 개요

- **서버**: 100.114.192.51 (기존 서버)
- **포트**: 58003 (bigkinds-mcp는 58002)
- **URL**: https://deepnews-oai.seolcoding.com

## 1. 서버 준비

```bash
# 서버 접속
ssh user@100.114.192.51

# 프로젝트 클론 (또는 복사)
cd /opt
git clone <repository-url> deep_news_oai
cd deep_news_oai
```

## 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 환경 변수 편집
vim .env
```

```env
BIGKINDS_USER_ID=your_user_id
BIGKINDS_USER_PASSWORD=your_password
LOG_LEVEL=INFO
```

## 3. Docker 네트워크 생성 (최초 1회)

```bash
# mcp-network가 없으면 생성
docker network create mcp-network
```

## 4. Docker 빌드 및 실행

```bash
# 빌드
docker-compose build

# 실행 (백그라운드)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 상태 확인
docker-compose ps
```

## 5. Health Check

```bash
# 로컬 테스트
curl http://localhost:58003/health

# 예상 응답
# {"status":"healthy","service":"deep-news-oai","client_initialized":true}
```

## 6. Cloudflare Tunnel 설정

기존 cloudflared 설정에 추가:

```bash
sudo vim /etc/cloudflared/config.yml
```

```yaml
ingress:
  - hostname: bigkinds.seolcoding.com
    service: http://localhost:58002
  - hostname: deepnews-oai.seolcoding.com  # 추가
    service: http://localhost:58003    # 추가
  - service: http_status:404
```

```bash
# 재시작
sudo systemctl restart cloudflared

# 상태 확인
sudo systemctl status cloudflared
```

## 7. ChatGPT 연결

1. ChatGPT 데스크탑 앱에서 Developer Mode 활성화
2. Settings > Developer Tools > MCP Servers
3. URL 입력: `https://deepnews.seolcoding.com/mcp`
4. Refresh 클릭하여 메타데이터 갱신

## 8. 운영 명령어

```bash
# 재시작
docker-compose restart

# 중지
docker-compose down

# 로그 (최근 100줄)
docker-compose logs --tail=100

# 실시간 로그
docker-compose logs -f

# 리빌드 및 재시작
docker-compose up -d --build
```

## 9. 문제 해결

### 컨테이너가 시작되지 않는 경우

```bash
# 상세 로그 확인
docker-compose logs deep-news-oai

# 환경 변수 확인
docker-compose config
```

### Health check 실패

```bash
# 직접 컨테이너 내부 접속
docker exec -it deep-news-oai bash

# 내부에서 확인
curl localhost:8000/health
```

### Cloudflare Tunnel 연결 안 됨

```bash
# Tunnel 상태 확인
cloudflared tunnel info <TUNNEL_NAME>

# DNS 확인
nslookup deepnews.seolcoding.com
```
