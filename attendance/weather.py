# weather.py
import requests
import json
from datetime import datetime, timedelta

def get_osaka_weather():
    """
    気象庁から大阪の天気情報を取得する
    
    Returns:
        dict: 今日と明日の天気情報を含む辞書
    """
    # 大阪のエリアコード
    area_code = "270000"
    
    API_KEY = "e44245e5f8c98c1e7b18f78edeab9c59"
    CITY = "Osaka"
    URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY},JP&appid={API_KEY}&units=metric"
    
    response = requests.get(URL)

    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        temp_rounded = round(temp, 1)
    else:
        print("エラー:", response.status_code)
        print("レスポンス内容:", response.text)
        
    # APIエンドポイント
    forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    overview_url = f"https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{area_code}.json"
    
    try:
        # 天気予報データの取得
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()
        
        # 概要データの取得
        overview_response = requests.get(overview_url)
        overview_data = overview_response.json()
        
        # 日付データを取得
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 天気情報の基本オブジェクト
        weather_info = {
            'today': {
                'date': today,
                'weather': '不明',
                'weather_code': '100',  # デフォルトは晴れ
                'temperature_min': None,
                'temperature_max': None,
                'icon_url': None
            },
            'tomorrow': {
                'date': tomorrow,
                'weather': '不明',
                'weather_code': '100',  # デフォルトは晴れ
                'temperature_min': None,
                'temperature_max': None,
                'icon_url': None
            },
            'overview': {
                'text': overview_data.get('text', '天気概要が取得できませんでした。'),
                'publishingOffice': overview_data.get('publishingOffice', '大阪管区気象台')
            }
        }
        
        # 時系列データから天気情報を取得
        if len(forecast_data) > 0 and 'timeSeries' in forecast_data[0]:
            time_series = forecast_data[0]['timeSeries']
            
            # 天気情報の取得
            for series in time_series:
                if 'areas' in series and len(series['areas']) > 0:
                    area = series['areas'][0]
                    
                    # 天気（一般的には最初の時系列）
                    if 'weathers' in area and 'weatherCodes' in area:
                        if len(area['weathers']) >= 1:
                            weather_info['today']['weather'] = area['weathers'][0]
                        if len(area['weathers']) >= 2:
                            weather_info['tomorrow']['weather'] = area['weathers'][1]
                        
                        if len(area['weatherCodes']) >= 1:
                            weather_info['today']['weather_code'] = area['weatherCodes'][0]
                            weather_info['today']['icon_url'] = f"https://www.jma.go.jp/bosai/forecast/img/{area['weatherCodes'][0]}.svg"
                        if len(area['weatherCodes']) >= 2:
                            weather_info['tomorrow']['weather_code'] = area['weatherCodes'][1]
                            weather_info['tomorrow']['icon_url'] = f"https://www.jma.go.jp/bosai/forecast/img/{area['weatherCodes'][1]}.svg"

                weather_info['today']['temperature'] = temp_rounded
        return weather_info
        
    except Exception as e:
        print(f"天気情報取得エラー: {e}")
        # エラー時はデフォルト値を返す
        return {
            'today': {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'weather': '情報取得エラー',
                'weather_code': '100',
                'temperature': None,
                'icon_url': "https://www.jma.go.jp/bosai/forecast/img/100.svg"
            },
            'overview': {
                'text': 'APIからの天気情報取得に失敗しました。',
                'publishingOffice': '大阪管区気象台'
            }
        }