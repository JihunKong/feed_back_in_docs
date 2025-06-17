# AI 문서 피드백 시스템

Google Docs 문서에 AI가 댓글로 상세한 피드백을 제공하는 시스템입니다.

## 기능

- Google Docs 문서 읽기 및 분석
- 전체 문서 구조 파악 및 섹션별 분석
- Claude AI를 활용한 지능적인 피드백
- 문서 타입별 맞춤형 피드백
- Google Docs에 직접 댓글 추가

## 설치 방법

### 로컬 환경

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 실행:
```bash
streamlit run app.py
```

### Streamlit Cloud 배포

1. GitHub에 저장소 생성
2. Streamlit Cloud에서 앱 생성
3. Secrets 설정:

```toml
# Streamlit Cloud secrets.toml
ANTHROPIC_API_KEY = "your-anthropic-api-key"

[google_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

## Google API 설정

1. [Google Cloud Console](https://console.cloud.google.com)에서 프로젝트 생성
2. Google Docs API 활성화
3. 서비스 계정 생성:
   - IAM & Admin > Service Accounts
   - CREATE SERVICE ACCOUNT
   - 키 생성 (JSON)
4. 서비스 계정 이메일에 Google Docs 편집 권한 부여

## 사용법

1. Google Docs 문서에 편집자 권한 부여 (서비스 계정 이메일)
2. 문서 URL 또는 ID 입력
3. 문서 타입과 피드백 초점 선택
4. 피드백 요청 버튼 클릭

## 개선된 기능

- **전체 문서 분석**: 문단별이 아닌 전체 문서를 분석하여 섹션별 피드백 제공
- **스마트 섹션 식별**: 문서 구조를 자동으로 파악하여 주요 섹션에만 피드백
- **Streamlit Cloud 최적화**: secrets.toml을 통한 간편한 배포

## 주의사항

- `secrets.toml` 파일은 절대 git에 커밋하지 마세요
- `.gitignore`에 `secrets.toml`이 포함되어 있는지 확인
- Google Docs에 편집자 권한이 있어야 댓글 추가 가능