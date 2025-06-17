import streamlit as st
import openai
import re
import time
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError

# 페이지 설정
st.set_page_config(
    page_title="AI 문서 피드백 시스템",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #17a2b8;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
    }
    .step-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
    }
    .feedback-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.markdown('<h1 class="main-header">📝 AI 문서 피드백 시스템</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Google Docs 문서에 AI가 파란색으로 첨삭 피드백을 제공합니다</p>', unsafe_allow_html=True)

# 사용법 안내
with st.expander("📖 사용법 안내", expanded=True):
    st.markdown("""
    ### 🚀 빠른 시작 가이드
    
    <div class='step-box'>
    <b>1단계: Google Docs 문서 준비</b>
    <ul>
    <li>피드백을 받고 싶은 Google Docs 문서를 준비합니다</li>
    <li>문서를 열고 우측 상단의 '공유' 버튼을 클릭합니다</li>
    <li>'링크 복사'를 클릭하거나, 특정 사용자에게 '편집자' 권한을 부여합니다</li>
    <li><b>중요:</b> 이 앱의 서비스 계정에 '편집자' 권한이 있어야 문서를 편집할 수 있습니다</li>
    </ul>
    </div>
    
    <div class='step-box'>
    <b>2단계: 문서 타입과 피드백 옵션 선택</b>
    <ul>
    <li>문서 타입 선택: 연구 보고서, 에세이, 제안서 등</li>
    <li>피드백 초점 선택: 논리성, 문법, 창의성 등</li>
    <li>각 옵션은 AI가 더 적절한 피드백을 제공하도록 돕습니다</li>
    </ul>
    </div>
    
    <div class='step-box'>
    <b>3단계: 피드백 요청</b>
    <ul>
    <li>Google Docs URL을 입력하고 '피드백 요청' 버튼을 클릭합니다</li>
    <li>AI가 문서를 분석하고 적절한 위치에 파란색으로 첨삭 내용을 삽입합니다</li>
    <li>Google Docs에서 파란색으로 표시된 첨삭 내용을 확인할 수 있습니다</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Google Docs 인증 설정
@st.cache_resource
def get_google_service():
    """Google Docs 서비스 인스턴스 생성"""
    try:
        # Streamlit secrets에서 가져오기 (Streamlit Cloud 우선)
        if "google_service_account" in st.secrets:
            service_account_info = st.secrets["google_service_account"]
            
            # 문서 편집을 위해 drive.file 권한 추가
            creds = Credentials.from_service_account_info(
                service_account_info,
                scopes=[
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
            
            service = build('docs', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            return service, drive_service
        else:
            st.error("⚠️ Google 서비스 계정 인증 정보가 필요합니다. Streamlit Cloud에서 secrets를 설정해주세요.")
            return None, None
    except Exception as e:
        st.error(f"Google 서비스 초기화 실패: {str(e)}")
        return None, None

def extract_document_id(url):
    """Google Docs URL에서 문서 ID 추출"""
    patterns = [
        r'/document/d/([a-zA-Z0-9-_]+)',
        r'/d/([a-zA-Z0-9-_]+)',
        r'docs\.google\.com/.*[?&]id=([a-zA-Z0-9-_]+)',
        r'^([a-zA-Z0-9-_]+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_document_content(service, document_id):
    """Google Docs 문서 내용과 구조 가져오기"""
    try:
        document = service.documents().get(documentId=document_id).execute()
        
        title = document.get('title', '제목 없음')
        content_with_positions = []
        full_document_text = []
        
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph_text = []
                start_index = element.get('startIndex', 0)
                end_index = element.get('endIndex', 0)
                
                for text_element in element['paragraph'].get('elements', []):
                    if 'textRun' in text_element:
                        text = text_element['textRun'].get('content', '')
                        if text.strip():
                            paragraph_text.append(text)
                
                if paragraph_text:
                    full_text = ''.join(paragraph_text)
                    content_with_positions.append({
                        'text': full_text,
                        'start': start_index,
                        'end': end_index
                    })
                    full_document_text.append(full_text)
        
        return title, content_with_positions, '\n'.join(full_document_text)
    except Exception as e:
        st.error(f"문서 읽기 오류: {str(e)}")
        return None, None, None

def analyze_document_structure(full_text):
    """문서의 구조를 분석하여 주요 섹션을 식별"""
    sections = []
    
    # 제목 패턴 (숫자나 특수 문자로 시작하는 줄)
    title_patterns = [
        r'^\d+\.\s+',  # 1. 2. 3. 등
        r'^\d+\)\s+',  # 1) 2) 3) 등
        r'^[IVX]+\.\s+',  # I. II. III. 등
        r'^\[.+\]\s*',  # [제목] 형식
        r'^#+\s+',  # # ## ### 마크다운 형식
    ]
    
    lines = full_text.split('\n')
    current_section = {'title': '서론', 'content': [], 'start_line': 0}
    
    for i, line in enumerate(lines):
        is_title = False
        
        # 빈 줄은 무시
        if not line.strip():
            if current_section['content']:
                current_section['content'].append(line)
            continue
        
        # 제목 패턴 확인
        for pattern in title_patterns:
            if re.match(pattern, line.strip()):
                is_title = True
                break
        
        # 대문자로만 이루어진 짧은 줄도 제목으로 간주
        if not is_title and line.strip().isupper() and len(line.strip()) < 50:
            is_title = True
        
        if is_title:
            # 이전 섹션 저장
            if current_section['content']:
                sections.append({
                    'title': current_section['title'],
                    'content': '\n'.join(current_section['content']),
                    'start_line': current_section['start_line'],
                    'end_line': i - 1
                })
            
            # 새 섹션 시작
            current_section = {
                'title': line.strip(),
                'content': [],
                'start_line': i
            }
        else:
            current_section['content'].append(line)
    
    # 마지막 섹션 저장
    if current_section['content']:
        sections.append({
            'title': current_section['title'],
            'content': '\n'.join(current_section['content']),
            'start_line': current_section['start_line'],
            'end_line': len(lines) - 1
        })
    
    # 섹션이 너무 많으면 내용을 기준으로 병합
    if len(sections) > 10:
        merged_sections = []
        current_merged = sections[0]
        
        for section in sections[1:]:
            # 짧은 섹션은 이전 섹션과 병합
            if len(section['content'].strip()) < 200:
                current_merged['content'] += '\n\n' + section['content']
                current_merged['end_line'] = section['end_line']
            else:
                merged_sections.append(current_merged)
                current_merged = section
        
        merged_sections.append(current_merged)
        sections = merged_sections
    
    return sections

def insert_feedback_to_doc(service, document_id, feedback_text, insert_index):
    """Google Docs에 파란색으로 첨삭 내용 삽입"""
    try:
        # 첨삭 내용을 파란색으로 삽입하기 위한 요청
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': insert_index
                    },
                    'text': f'\n[첨삭: {feedback_text}]\n'
                }
            },
            {
                'updateTextStyle': {
                    'range': {
                        'startIndex': insert_index,
                        'endIndex': insert_index + len(f'\n[첨삭: {feedback_text}]\n')
                    },
                    'textStyle': {
                        'foregroundColor': {
                            'color': {
                                'rgbColor': {
                                    'red': 0.0,
                                    'green': 0.0,
                                    'blue': 1.0
                                }
                            }
                        },
                        'italic': True,
                        'fontSize': {
                            'magnitude': 10,
                            'unit': 'PT'
                        }
                    },
                    'fields': 'foregroundColor,italic,fontSize'
                }
            }
        ]
        
        service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return True
    except HttpError as e:
        if e.resp.status == 403:
            st.error("❌ 문서를 편집할 권한이 없습니다. 문서에 '편집자' 권한을 부여해주세요.")
        else:
            st.error(f"첨삭 내용 삽입 중 오류 발생: {str(e)}")
        return False
    except Exception as e:
        st.error(f"첨삭 내용 삽입 중 오류 발생: {str(e)}")
        return False

# 문서 타입과 피드백 초점 옵션
DOCUMENT_TYPES = {
    "연구 보고서": "학술적 연구 보고서로서 논리성, 근거의 타당성, 연구 방법론을 중점적으로",
    "에세이": "에세이로서 주장의 명확성, 논거의 설득력, 문장의 흐름을 중점적으로",
    "제안서": "비즈니스 제안서로서 목표의 명확성, 실행 가능성, 예상 효과를 중점적으로",
    "기술 문서": "기술 문서로서 정확성, 명확성, 구조의 체계성을 중점적으로",
    "창작물": "창작물로서 창의성, 표현력, 독자 몰입도를 중점적으로"
}

FEEDBACK_FOCUS = {
    "종합적 피드백": "전반적인 관점에서 균형잡힌",
    "논리성 및 구조": "논리적 흐름과 구조적 완성도 위주의",
    "문법 및 표현": "문법적 정확성과 표현의 적절성 위주의",
    "내용의 깊이": "주제의 심층적 탐구와 분석의 깊이 위주의",
    "창의성 및 독창성": "새로운 관점과 창의적 접근 위주의",
    "실용성 및 적용성": "실제 적용 가능성과 실용적 가치 위주의"
}

# 사이드바 설정
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    
    # API 키 입력 (Streamlit secrets 우선)
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    
    if not api_key:
        api_key = st.text_input("OpenAI API Key", type="password", help="OpenAI API 키를 입력하세요")
    
    # GPT-4o-mini 모델 고정
    model_choice = "gpt-4o-mini"
    st.info(f"🤖 사용 모델: {model_choice}")
    
    st.markdown("---")
    
    # 문서 타입 선택
    doc_type = st.selectbox(
        "📄 문서 타입",
        list(DOCUMENT_TYPES.keys()),
        help="분석할 문서의 종류를 선택하세요"
    )
    
    # 피드백 초점 선택
    feedback_focus = st.selectbox(
        "🎯 피드백 초점",
        list(FEEDBACK_FOCUS.keys()),
        help="AI가 집중해서 분석할 영역을 선택하세요"
    )
    
    # 추가 지시사항
    custom_instructions = st.text_area(
        "📝 추가 지시사항 (선택)",
        placeholder="AI에게 특별히 요청하고 싶은 사항이 있다면 입력하세요",
        help="예: '초등학생도 이해할 수 있는 쉬운 언어로 피드백 부탁해', '영어 표현에 대한 조언도 포함해주세요' 등"
    )
    
    st.markdown("---")
    st.markdown("### 🔍 시스템 상태")
    
    # API 키 상태
    if api_key:
        st.success("✅ OpenAI API 연결됨")
    else:
        st.warning("⚠️ API 키 필요")
    
    # Google 서비스 상태
    if "google_service_account" in st.secrets:
        st.success("✅ Google API 연결됨")
    else:
        st.warning("⚠️ Google 인증 필요")

# 메인 컨텐츠
st.markdown("### 📄 문서 정보 입력")

# 현재 설정 표시
col1, col2 = st.columns(2)
with col1:
    st.info(f"**문서 타입:** {doc_type}")
with col2:
    st.info(f"**피드백 초점:** {feedback_focus}")

# Google Docs URL 입력
doc_url = st.text_input(
    "Google Docs 문서 URL 또는 ID",
    placeholder="https://docs.google.com/document/d/YOUR_DOCUMENT_ID/edit",
    help="편집자 권한이 부여된 Google Docs 링크를 입력하세요"
)

# 예시 문서 정보
with st.expander("💡 테스트용 예시 문서"):
    st.markdown("""
    테스트를 위한 예시 문서: 
    
    https://docs.google.com/document/d/1DMTbJjOafh-guixzR6uagAWNwOhM1oAI0M_QMPwWpFM/edit?tab=t.0#heading=h.2lzghcnx3r3a
    
    **주의:** 이 문서에 편집자 권한을 부여해야 첨삭 기능이 작동합니다.
    """)

# 피드백 요청 버튼
if st.button("🚀 피드백 요청", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠️ API 키를 입력해주세요!")
    elif not doc_url:
        st.error("⚠️ Google Docs URL을 입력해주세요!")
    else:
        # 문서 ID 추출
        document_id = extract_document_id(doc_url)
        
        if not document_id:
            st.error("⚠️ 유효한 Google Docs URL이 아닙니다!")
        else:
            # Google 서비스 가져오기
            docs_service, drive_service = get_google_service()
            
            if docs_service:
                with st.spinner("📖 문서를 읽어오는 중..."):
                    title, content_with_positions, full_text = get_document_content(docs_service, document_id)
                
                if content_with_positions and full_text:
                    st.success(f"✅ 문서 로드 완료: **{title}**")
                    
                    # 내용 미리보기
                    with st.expander("📄 문서 내용 미리보기", expanded=False):
                        st.text(full_text[:1000] + "..." if len(full_text) > 1000 else full_text)
                    
                    # 문서 구조 분석
                    sections = analyze_document_structure(full_text)
                    
                    # 전체 문서 분석
                    with st.spinner("🤖 전체 문서를 분석하고 있습니다..."):
                        try:
                            # OpenAI 클라이언트 설정
                            openai.api_key = api_key
                            
                            # 전체 문서에 대한 분석 요청
                            analysis_prompt = f"""
                            다음은 {doc_type}의 전체 내용입니다.
                            {DOCUMENT_TYPES[doc_type]} 평가해주세요.
                            {FEEDBACK_FOCUS[feedback_focus]} 피드백을 제공해주세요.
                            
                            {f"추가 지시사항: {custom_instructions}" if custom_instructions else ""}
                            
                            문서 내용:
                            {full_text}
                            
                            위 문서를 분석하여 다음과 같은 형식으로 피드백을 제공해주세요:
                            
                            1. 전체적인 평가 (2-3문장)
                            2. 주요 강점 3가지
                            3. 개선이 필요한 부분 3-5가지 (각각 해당 섹션명과 함께)
                            4. 추가 제안사항
                            
                            각 항목에 대해 구체적이고 건설적인 피드백을 한국어로 작성해주세요.
                            """
                            
                            response = openai.ChatCompletion.create(
                                model=model_choice,
                                messages=[{
                                    "role": "system",
                                    "content": "당신은 전문적인 문서 분석가입니다. 구체적이고 건설적인 피드백을 제공합니다."
                                }, {
                                    "role": "user",
                                    "content": analysis_prompt
                                }],
                                max_tokens=2000,
                                temperature=0.7
                            )
                            
                            full_analysis = response.choices[0].message.content
                            
                        except Exception as e:
                            st.error(f"문서 분석 중 오류 발생: {str(e)}")
                            full_analysis = "분석을 수행할 수 없습니다."
                    
                    # 분석 결과 표시
                    st.markdown("📊 **문서 분석 결과**")
                    with st.expander("📑 전체 분석 보기", expanded=True):
                        st.markdown(full_analysis)
                    
                    # 진행 상황 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 첨삭 내용을 삽입할 위치 계산 (역순으로 삽입해야 인덱스가 꼬이지 않음)
                    feedback_insertions = []
                    
                    # 작지만 의미 있는 섹션들을 필터링
                    meaningful_sections = [s for s in sections if len(s['content'].strip()) > 200]
                    
                    # 상위 5-7개 섹션에만 피드백 추가
                    sections_to_feedback = meaningful_sections[:min(7, len(meaningful_sections))]
                    
                    # 먼저 모든 피드백을 생성하고 위치 파악
                    for idx, section in enumerate(sections_to_feedback):
                        progress = (idx + 1) / (len(sections_to_feedback) * 2)  # 분석은 전체의 50%
                        progress_bar.progress(progress)
                        status_text.text(f"🤖 '{section['title'][:30]}...' 섹션 분석 중...")
                        
                        try:
                            # 해당 섹션에 대한 구체적인 피드백
                            section_prompt = f"""
                            다음은 '{section['title']}' 섹션의 내용입니다:
                            
                            {section['content'][:1000]}...
                            
                            이 섹션에 대해 구체적이고 건설적인 피드백을 2-3문장으로 제공해주세요.
                            개선 방향이나 구체적인 예시를 포함해주세요.
                            """
                            
                            feedback_response = openai.ChatCompletion.create(
                                model=model_choice,
                                messages=[{
                                    "role": "system",
                                    "content": "당신은 전문적인 문서 첨삭 전문가입니다. 간결하고 구체적인 피드백을 제공합니다."
                                }, {
                                    "role": "user",
                                    "content": section_prompt
                                }],
                                max_tokens=300,
                                temperature=0.7
                            )
                            
                            section_feedback = feedback_response.choices[0].message.content
                            
                            # 해당 섹션의 위치 찾기
                            section_start_text = section['content'][:100].strip()
                            for para in content_with_positions:
                                if section_start_text in para['text']:
                                    # 섹션 끝 위치에 피드백 삽입 예약
                                    feedback_insertions.append({
                                        'index': para['end'],
                                        'feedback': section_feedback,
                                        'section_title': section['title']
                                    })
                                    break
                            
                            # API 호출 제한을 위한 짧은 대기
                            time.sleep(1)
                            
                        except Exception as e:
                            st.warning(f"섹션 '{section['title'][:30]}...' 분석 중 오류: {str(e)}")
                    
                    # 역순으로 정렬 (뒤에서부터 삽입해야 인덱스가 변하지 않음)
                    feedback_insertions.sort(key=lambda x: x['index'], reverse=True)
                    
                    # 첨삭 내용 삽입
                    feedback_added = 0
                    for i, insertion in enumerate(feedback_insertions):
                        progress = 0.5 + (i + 1) / (len(feedback_insertions) * 2)  # 삽입은 나머지 50%
                        progress_bar.progress(progress)
                        status_text.text(f"🖍️ '{insertion['section_title'][:30]}...' 섹션에 첨삭 내용 삽입 중...")
                        
                        if insert_feedback_to_doc(docs_service, document_id, 
                                                insertion['feedback'], 
                                                insertion['index']):
                            feedback_added += 1
                        
                        # API 호출 제한을 위한 짧은 대기
                        time.sleep(0.5)
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ 분석 완료!")
                    
                    if feedback_added > 0:
                        st.markdown(f"""
                        <div class='success-box'>
                        <h4>✅ 첨삭 완료!</h4>
                        <p>총 {feedback_added}개의 파란색 첨삭 내용이 문서에 삽입되었습니다.</p>
                        <p>Google Docs에서 파란색으로 표시된 첨삭 내용을 확인하세요!</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 문서 링크 제공
                        st.markdown(f"[📄 Google Docs에서 열기](https://docs.google.com/document/d/{document_id}/edit)")
                    else:
                        st.warning("⚠️ 첨삭 내용을 추가하지 못했습니다. 문서 권한을 확인해주세요.")
                else:
                    st.error("❌ 문서 내용을 가져올 수 없습니다. 문서 권한을 확인해주세요.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        <p>Powered by OpenAI GPT-4o-mini & Google Docs API | 교육 목적으로 제작됨</p>
        <p style='font-size: 0.8rem; margin-top: 0.5rem;'>
            Streamlit Cloud에서 secrets.toml을 통해 API 키를 설정하세요
        </p>
    </div>
    """,
    unsafe_allow_html=True
)