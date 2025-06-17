# AI 문서 첨삭 시스템

Google Docs 문서에 AI가 파란색으로 첨삭 피드백을 제공하는 시스템입니다.

## 기능

- Google Docs 문서 읽기 및 분석
- 전체 문서 구조 파악 및 섹션별 분석
- OpenAI GPT-4o-mini를 활용한 지능적인 피드백
- 문서 타입별 맞춤형 피드백
- Google Docs에 파란색 텍스트로 첨삭 내용 삽입

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
OPENAI_API_KEY = "your-openai-api-key"

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
5. 문서에 파란색으로 첨삭 내용이 삽입됨

## 개선된 기능

- **전체 문서 분석**: 문단별이 아닌 전체 문서를 분석하여 섹션별 피드백 제공
- **파란색 첨삭**: 댓글이 아닌 문서에 직접 파란색 텍스트로 첨삭 내용 삽입
- **스마트 섹션 식별**: 문서 구조를 자동으로 파악하여 주요 셉션에만 피드백
- **Streamlit Cloud 최적화**: secrets.toml을 통한 간편한 배포
- **GPT-4o-mini 모델 사용**: 빠르고 효율적인 AI 피드백

## 주의사항

- `secrets.toml` 파일은 절대 git에 커밋하지 마세요
- `.gitignore`에 `secrets.toml`이 포함되어 있는지 확인
- Google Docs에 편집자 권한이 있어야 문서 편집 가능