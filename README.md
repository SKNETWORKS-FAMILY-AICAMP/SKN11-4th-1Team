# SKN11-4th-1Team

<br/>

# 1. 팀 소개

### 팀명 : 🚨사고 정찰단


# 🫡 팀원 소개
| <div align="center">[성호진](https://github.com/DawnSurplus)</div> | <div align="center">[신진슬](https://github.com/SHINJINSEUL)</div> | <div align="center">[이채은](https://github.com/chaeeunlee05)</div> | <div align="center">[방성일](https://github.com/SungilBang12)</div> | <div align="center">[이선호](https://github.com/Seonh0)</div> |
|--------|--------|--------|--------|--------|
| <img src="./img/성호진.png" width="120" height="120"/><br> | <img src="./img/신진슬.png" width="120" height="120"/><br> | <img src="./img/이채은.png" width="120" height="120"/><br> | <img src="./img/방성일.png" width="120" height="120"/><br> | <img src="./img/이선호.png" width="120" height="120"/><br> |


<br/><br/>

# 2. 프로젝트 개요

<aside>

### 프로젝트 명 < `교통사고 과실비율 산정 AI 챗봇 <노느>` >


<p align="center">
  <img src="./img/article1.png" width="250"/>
  <img src="./img/노느Logo.png" width="180"/>
  <img src="./img/article2.png" width="250"/>
</p>


</aside>

### 프로젝트 소개

- 교통사고 발생 시 법률 기준과 판례를 기반으로 **과실비율을 신속하게 산정**해주는 AI 챗봇
- 사용자가 사고 상황을 입력하면, 도로교통법, 대법원 판례 등 **복잡한 법률 자료를 자동으로 분석**하여 기본 과실비율과 그에 대한 판단 근거를 제시함.

<br/>

### 프로젝트 필요성(배경)

1. **과실비율 합의의 어려움**
    
    ![<출처 : 과실비율정보포털>](./img/과실분쟁_발생이유.png)
    
    <출처 : 과실비율정보포털>
    
        
    - 연간 126만 건 이상의 교통사고 발생 시, 당사자 간 주관적 주장으로 인한 분쟁 증가
    - **객관적 기준이 아닌 감정과 오해에 기반한 과실 주장 증가**로 인해, 법적 판단과 다른 무리한 요구가 빈번히 발생하며 공정하고 신속한 과실 산정을 어렵게 만듦
2. 일반인이 이해하기 어려운 법
    - 과실비율이 산정은 전문 지식이 필요한 도로교통법, 민법, 보험약관, 판례 등을 바탕으로 진행
        
    
    - 일반인의 이해 한계로 인해 **불공정한 합의가 이뤄질 가능성**이 큼.
3. **판례 검색의 한계**
    - 사고당사자가 수많은 판례 중에서 자신의 상황에 맞는 사례를 직접 검색하고 법리적 근거를 해석하기란 매우 어렵고 시간이 많이 소요됨.

<br/>  

### 프로젝트 목표

- 일반 개인이 **사고 상황 입력만으로 근거 있는 과실 비율을 신속히 제공하는 챗봇** 개발
- **도로교통법, 용어, 판례 등의 설명을 질의응답 형태로 제공하는 챗봇** 개발
- **사용자 친화적인 시스템을 구축 및 웹서비스로 제공**하여 과실비율 산정에 대한 이해도를 높임

<br/><br/>



# 3. WBS
![image.png](./img/WBS.png)

<br/><br/>



# 4. [요구사항 명세서🔗](./output/요구사항%20명세서%20작성.pdf)

`[예시 - 메인 페이지]`

![image.png](./img/요구사항%20명세서%20예시.png)

<br/><br/>



# 5. 기술 스택 & 사용한 모델 (임베딩 모델, LLM)


| 카테고리 | 기술 스택 |
|----------|------------|
| Language | ![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white) |
| Development | ![VS Code](https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white) |
| Embedding Model | ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)|
| Vector DB | ![ChromaDB](https://img.shields.io/badge/ChromaDB-3E5F8A?style=for-the-badge&logo=databricks&logoColor=white) |
| Database | ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white) |
| LLM Model | ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white) |
| Framework | ![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white) ![LangChain](https://img.shields.io/badge/LangChain-F9A825?style=for-the-badge&logoColor=white)|
| Deployment | ![AWS EC2](https://img.shields.io/badge/AWS%20EC2-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white) |
| Collaboration Tool | ![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white) ![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white) ![Notion](https://img.shields.io/badge/Notion-181717?style=for-the-badge&logo=notion&logoColor=white) |


<br/><br/>

# 6. 시스템 아키텍처


![image.png](./img/systemarchitecture.png)

<br/>

# 7. 시스템 워크플로우


![image.png](./img/systemworkflow.jpg)


<br/><br/>

# 8. [화면 정의서🔗](./output/screen%20definition.pdf)

## `Main 채팅 화면` ##
![image.png](./img/chat.png)

## `login 화면` ##
![image.png](./img/login.png)

## `community 화면` ##
![image.png](./img/community.png)

## `signup 화면` ##
![image.png](./img/signup.png)

<br/><br/>

# 9. 수행결과(테스트/시연 페이지)

`Image 클릭 시 AWS 배포 port번호로 이동`

[![image.png](./img/수행결과.png)](http://15.165.222.110:8080/)

<br/><br/>

# 10. [테스트 계획 및 결과 보고서🔗](./output/test_result_report.pdf)

## 메인 페이지
![image.png](./img/result_main.png)

## 커뮤니티 페이지
![image.png](./img/result_community1.png)

## 댓글 페이지
![image.png](./img/result_comment.png)

<br/><br/>

# 11. 3차 프로젝트 대비 개선사항
## 🤖 AI 시스템 개선

### 🧩 1. API 호출 최적화
- **📌 개선**:  
  3단계 → 1단계 호출 통합  
  *(분류 API → 처리 API → 응답 생성 → 하나로 통합)*
- **🎯 이유**:  
  OpenAI API 호출 횟수로 인해 **비용 증가** + **속도 지연**
- **✅ 효과**:
  - **비용 66% 절감** (월 $300 → $100)
  - **응답속도 향상** (10~15초 → 3~5초)

---

### 🧠 2. 파인튜닝 모델 적용 (GPT-3.5-turbo)
- **📌 개선**:  
  교통사고 관련 질문 카테고리 분류용 데이터로 **파인튜닝**
- **✅ 효과**:
  - **도메인 특화된 분류 정확도 향상**
  - **복잡한 질문에 대한 처리 능력 향상**

---

### 🔀 3. 하이브리드 질의 분류 시스템
- **📌 구조**:  
  `키워드 기반 95%` + `AI 모델 기반 5%`
  - ① **1차 분류**: 키워드 점수화 (0.1초 응답, 비용 0원)
  - ② **2차 분류**: GPT-3.5-turbo 사용 (복합/애매한 질문만)
- **🎯 이유**:  
  단순 질문까지 AI 호출은 **비효율**
- **✅ 효과**:
  - **분류비용 95% 감소**
  - **즉시 응답 + 정확도 유지**
  - **유연한 키워드 패턴 확장 가능**

---

### 🧵 4. 세션 기반 대화 맥락 이해
- **📌 개선**:
  - 최근 **8개 대화쌍** 저장하여 맥락 유지
  - "그것", "해당", "이 사고" 등 **지시어/대명사 해석**
  - **전문성 자동 조정** (초보자 ↔ 전문가)
- **✅ 효과**:
  - **자연스러운 대화 흐름**
  - **사용자 맞춤형 설명**
  - **상담 시간 단축 + 반복 설명 감소**

---

### 🧭 5. 하이브리드 RAG 검색
- **📌 구성**:
  - **Direct Search**: ChromaDB 벡터 유사도 (빠름)
  - **Self-Query Search**: LangChain 기반 메타데이터 필터링
- **🎯 이유**:  
  벡터 검색의 **한계**와 **정확도 부족**
- **✅ 효과**:
  - **검색 정확도 상승**
  - **법원명·사건번호·조문 등 정밀 검색 가능**

---

## 🌐 웹 시스템 개선

### 1. WebSocket 실시간 채팅 도입
- **📌 개선**:  
  HTTP → WebSocket 양방향 비동기 통신
- **🎯 이유**:  
  요청-응답 대기 구조의 비효율성 제거
- **✅ 효과**:
  - **답변 실시간 확인**
  - **자연스러운 챗봇 경험**

---



<br/><br/>

# 한 줄 회고

### 호진

- 이번 프로젝트에서는 웹 페이지를 구현하고 배포하는 부분에 비중을 두었다. 웹 part는 처음 접하는 부분이었는데, 만들고자 하는 페이지의 요구사항을 구체화하고 실제 구현 및 AWS 배포까지 이어지는 과정을 경험할 수 있었고, 무사히 프로젝트 마무리되어 좋은 경험이 되었다.

### 성일

- 웹페이지 작성을 통해 html의 구조와 django, aws의 ec2 서버와 RDS를 사용해 보면서, 우리가 사용하는 웹페이지가 이런 과정을 통해 만들어지는구나 하고 새삼스럽게 감탄했다. 일을 하면서 실력이 부족해 끝내지 못하고 다른 분들에게 부탁 드린 것이 많았는데, 책임을 다하려면 기능의 구현에 어떤 에러가 발생할 수 있는지, 그렇다면 그 해결방안은 무엇인지 등을 사용 툴이 정해졌을 때 조사해보며 미리미리 준비하는 태도를 지녀야겠다. 

### 채은

- 이번 4차 프로젝트에서는 Django를 이용해 사용자의 편의성과 접근성을 고려한 웹페이지를 구현했습니다. 또한 AWS를 활용해 실제 서비스로 배포하는 과정까지 직접 경험하며 개발부터 운영까지 전체적인 흐름을 이해할 수 있었습니다.

### 진슬

- 4차 프로젝트에서는 Django를 활용해 교통사고 과실비율 상담 챗봇 웹 페이지를 구축하고, 기능별 앱 분리와 템플릿 구조 설계를 통해 역할을 명확히 나눴다.
커뮤니티 기능에서는 글쓰기, 댓글, 좋아요 구현뿐 아니라 Bootstrap 연동과 검색/페이징 기능을 적용해 사용자 편의성과 실용성을 높였다.
또한 RAG 기반 과실비율 판단 시스템과 연계하여, 챗봇의 사고 상황 분석 결과를 UI에 자연스럽게 연결하는 경험을 통해 Django 웹 서비스의 흐름을 심도 있게 이해할 수 있었다.



### 선호

- 파인튜닝부터 Django, AWS를 통한 AI 모델 서빙에 대해서 다양한 시행착오를 겪어보며 실력을 늘릴 수 있는 기회가 되어서 좋았습니다!