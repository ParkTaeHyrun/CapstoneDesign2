from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import uvicorn
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import tensorflow as tf
import keras
from keras import layers
from sklearn.preprocessing import StandardScaler

app = FastAPI(title="지진 예측 API")

# 전역 변수
model = None
earthquake_data = None
scaler = StandardScaler()
geolocator = Nominatim(user_agent="earthquake_prediction")

def create_model():
    """딥러닝 모델 생성"""
    model = keras.Sequential([
        layers.Dense(64, activation='relu', input_shape=(2,)),
        layers.Dropout(0.2),
        layers.Dense(32, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(16, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(8, activation='softmax')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

def initialize_data():
    """데이터 로드 및 전처리"""
    global earthquake_data
    try:
        df = pd.read_csv('earthquake_data.csv', encoding='utf-8')
        df = df[['위도', '경도', '규모']].dropna()
        
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df['규모'] = pd.to_numeric(df['규모'], errors='coerce')
        
        df = df[
            (df['위도'].between(33, 43)) &
            (df['경도'].between(124, 132)) &
            (df['규모'].between(2.0, 7.0))
        ]
        
        if len(df) == 0:
            raise ValueError("유효한 데이터가 없습니다.")
            
        earthquake_data = df
        print(f"데이터 로드 완료: {len(df)}개의 지진 기록")
        return True
    except Exception as e:
        print(f"데이터 초기화 오류: {str(e)}")
        return False

def prepare_magnitude_labels(magnitudes):
    """지진 규모를 범위별로 분류"""
    labels = np.zeros(len(magnitudes))
    for i, mag in enumerate(magnitudes):
        if 2.0 <= mag < 2.5: labels[i] = 0
        elif 2.5 <= mag < 3.0: labels[i] = 1
        elif 3.0 <= mag < 3.5: labels[i] = 2
        elif 3.5 <= mag < 4.0: labels[i] = 3
        elif 4.0 <= mag < 4.5: labels[i] = 4
        elif 4.5 <= mag < 5.0: labels[i] = 5
        elif 5.0 <= mag < 5.5: labels[i] = 6
        else: labels[i] = 7
    return labels

def train_model(latitude: float, longitude: float, radius_km: float = 100):
    """특정 위치 주변의 데이터로 모델 학습"""
    global model, earthquake_data, scaler
    
    if not (33 <= latitude <= 43) or not (124 <= longitude <= 132):
        return False, "한국 영역 밖의 좌표입니다."
    
    lat_range = radius_km / 111
    lon_range = radius_km / (88.6 * np.cos(np.radians(latitude)))
    
    mask = (
        (earthquake_data['위도'] >= latitude - lat_range) &
        (earthquake_data['위도'] <= latitude + lat_range) &
        (earthquake_data['경도'] >= longitude - lon_range) &
        (earthquake_data['경도'] <= longitude + lon_range)
    )
    
    nearby_data = earthquake_data[mask]
    
    if len(nearby_data) < 10:
        return False, f"데이터 부족 (필요: 10개 이상, 현재: {len(nearby_data)}개)"
    
    X = nearby_data[['위도', '경도']].values
    y = prepare_magnitude_labels(nearby_data['규모'].values)
    X = scaler.fit_transform(X)
    
    model = create_model()
    
    if len(nearby_data) < 100:
        X_aug = X.copy()
        y_aug = y.copy()
        for _ in range(5):
            noise = np.random.normal(0, 0.01, X.shape)
            X_aug = np.vstack([X_aug, X + noise])
            y_aug = np.concatenate([y_aug, y])
        X = X_aug
        y = y_aug
    
    model.fit(X, y, epochs=100, batch_size=32, validation_split=0.2, verbose=0)
    return True, f"학습 완료 (학습 데이터: {len(nearby_data)}개)"

def predict_magnitude_probabilities(latitude: float, longitude: float):
    """지진 규모 범위별 발생 확률 예측"""
    global model, scaler
    
    X = np.array([[latitude, longitude]])
    X = scaler.transform(X)
    probabilities = model.predict(X, verbose=0)[0]
    
    magnitude_ranges = [
        "2.0-2.5", "2.5-3.0", "3.0-3.5", "3.5-4.0",
        "4.0-4.5", "4.5-5.0", "5.0-5.5", "5.5-6.0"
    ]
    
    result = {}
    for range_name, prob in zip(magnitude_ranges, probabilities):
        min_prob = 0.001
        adjusted_prob = max(float(prob), min_prob)
        result[range_name] = round(adjusted_prob * 100, 2)
    
    total_prob = sum(result.values())
    if total_prob > 0:
        for range_name in result:
            result[range_name] = round(result[range_name] * 100 / total_prob, 2)
    
    return result

def get_address(latitude: float, longitude: float) -> str:
    """위도/경도를 도로명 주소로 변환"""
    try:
        location = geolocator.reverse(f"{latitude}, {longitude}", language='ko')
        return location.address if location else "주소를 찾을 수 없습니다."
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"주소 변환 오류: {str(e)}")
        return "주소 변환 중 오류가 발생했습니다."

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    if not initialize_data():
        raise Exception("데이터 초기화 실패")

@app.get("/")
async def root():
    return {"메시지": "지진 예측 API 서버에 오신 것을 환영합니다!"}

@app.get("/earthquake/{latitude}/{longitude}")
async def get_earthquake_info(latitude: float, longitude: float):
    try:
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="잘못된 위도/경도 값입니다.")
        
        address = get_address(latitude, longitude)
        success, message = train_model(latitude, longitude)
        
        if not success:
            return {
                "상태": "데이터부족",
                "위치": {"위도": latitude, "경도": longitude, "주소": address},
                "메시지": message,
                "데이터_상태": {
                    "총_지진_기록": len(earthquake_data),
                    "데이터_범위": {
                        "위도": [float(earthquake_data['위도'].min()), float(earthquake_data['위도'].max())],
                        "경도": [float(earthquake_data['경도'].min()), float(earthquake_data['경도'].max())],
                        "규모": [float(earthquake_data['규모'].min()), float(earthquake_data['규모'].max())]
                    }
                }
            }
        
        probabilities = predict_magnitude_probabilities(latitude, longitude)
        max_prob_range = max(probabilities.items(), key=lambda x: x[1])
        
        risk_levels = {
            "2.0-2.5": ("낮음", "일상생활에 영향 없음"),
            "2.5-3.0": ("낮음", "일상생활에 영향 없음"),
            "3.0-3.5": ("보통", "약간의 진동 감지 가능"),
            "3.5-4.0": ("보통", "약간의 진동 감지 가능"),
            "4.0-4.5": ("높음", "건물 피해 가능성 있음"),
            "4.5-5.0": ("높음", "건물 피해 가능성 있음"),
            "5.0-5.5": ("매우 높음", "심각한 피해 가능성 있음"),
            "5.5-6.0": ("매우 높음", "심각한 피해 가능성 있음")
        }
        
        risk_level, risk_description = risk_levels[max_prob_range[0]]
        
        lat_range = 100 / 111
        lon_range = 100 / (88.6 * np.cos(np.radians(latitude)))
        
        mask = (
            (earthquake_data['위도'] >= latitude - lat_range) &
            (earthquake_data['위도'] <= latitude + lat_range) &
            (earthquake_data['경도'] >= longitude - lon_range) &
            (earthquake_data['경도'] <= longitude + lon_range)
        )
        
        nearby_data = earthquake_data[mask]
        
        return {
            "상태": "성공",
            "위치": {"위도": latitude, "경도": longitude, "주소": address},
            "예측결과": {
                "규모별_발생확률": probabilities,
                "가장_높은_확률의_규모": max_prob_range[0],
                "위험도": {"수준": risk_level, "설명": risk_description}
            },
            "과거데이터": {
                "총지진수": len(nearby_data),
                "평균규모": round(float(nearby_data['규모'].mean()), 2),
                "최대규모": round(float(nearby_data['규모'].max()), 2),
                "최소규모": round(float(nearby_data['규모'].min()), 2),
                "최근_지진": {
                    "최대규모_지진": {
                        "규모": round(float(nearby_data['규모'].max()), 2),
                        "위도": float(nearby_data.loc[nearby_data['규모'].idxmax(), '위도']),
                        "경도": float(nearby_data.loc[nearby_data['규모'].idxmax(), '경도'])
                    }
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000) 