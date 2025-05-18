# 지진 예측 API 서버

FastAPI를 사용한 지진 예측 API 서버입니다.

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 서버 실행:
```bash
uvicorn main:app --reload
```

## API 엔드포인트

- `GET /`: 메인 페이지
- `GET /health`: 서버 상태 확인

## API 문서

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 