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
                    
                    # 気温データの取得
                    if 'temps' in area or 'tempsMin' in area or 'tempsMax' in area:
                        if 'temps' in area and len(area['temps']) >= 4:
                            # この形式の場合は、今日の最低気温、今日の最高気温、明日の最低気温、明日の最高気温の順
                            weather_info['today']['temperature_min'] = area['temps'][0]
                            weather_info['today']['temperature_max'] = area['temps'][1]
                            weather_info['tomorrow']['temperature_min'] = area['temps'][2]
                            weather_info['tomorrow']['temperature_max'] = area['temps'][3]
                        elif 'tempsMin' in area and 'tempsMax' in area:
                            # 最低気温と最高気温が別々のフィールドに格納されている場合
                            if len(area['tempsMin']) >= 2 and len(area['tempsMax']) >= 2:
                                weather_info['today']['temperature_min'] = area['tempsMin'][0]
                                weather_info['today']['temperature_max'] = area['tempsMax'][0]
                                weather_info['tomorrow']['temperature_min'] = area['tempsMin'][1]
                                weather_info['tomorrow']['temperature_max'] = area['tempsMax'][1]
        
        return weather_info
        
    except Exception as e:
        print(f"天気情報取得エラー: {e}")
        # エラー時はデフォルト値を返す
        return {
            'today': {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'weather': '情報取得エラー',
                'weather_code': '100',
                'temperature_min': None,
                'temperature_max': None,
                'icon_url': "https://www.jma.go.jp/bosai/forecast/img/100.svg"
            },
            'tomorrow': {
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'weather': '情報取得エラー',
                'weather_code': '100',
                'temperature_min': None,
                'temperature_max': None,
                'icon_url': "https://www.jma.go.jp/bosai/forecast/img/100.svg"
            },
            'overview': {
                'text': 'APIからの天気情報取得に失敗しました。',
                'publishingOffice': '大阪管区気象台'
            }
        }

def get_weather_advice(weather_text, weather_code, temp_max=None):
    """
    天気情報に基づいて、適切なアドバイスを返す
    
    Args:
        weather_text (str): 天気の説明テキスト
        weather_code (str): 天気コード
        temp_max (str, optional): 最高気温. デフォルトはNone
    
    Returns:
        str: アドバイステキスト
    """
    # 雨の場合
    if '雨' in weather_text or weather_code.startswith('3') or weather_code.startswith('4'):
        return '<i class="fas fa-umbrella"></i> 今日は雨の予報です。傘を忘れずに持っていきましょう！また、足元がぬれているかもしれないので、滑らないように注意してください。'
    
    # 雪の場合
    elif '雪' in weather_text or weather_code.startswith('6') or weather_code.startswith('7'):
        return '<i class="fas fa-snowflake"></i> 今日は雪の予報です。暖かい服装と滑りにくい靴で出かけましょう。路面が凍結している場合があるので、歩行時や運転時は十分注意してください。'
    
    # 雷の場合
    elif '雷' in weather_text or weather_code.startswith('8'):
        return '<i class="fas fa-bolt"></i> 今日は雷を伴う天気です。外出時は十分に注意し、できるだけ建物の中で過ごすようにしましょう。'
    
    # 曇りの場合
    elif '曇' in weather_text or weather_code.startswith('2'):
        return '<i class="fas fa-cloud"></i> 今日は曇りの予報です。急な天候の変化に備えて、折りたたみ傘があると安心かもしれません。'
    
    # 晴れの場合
    elif '晴' in weather_text or weather_code.startswith('1'):
        if temp_max and temp_max.isdigit() and int(temp_max) > 28:
            return '<i class="fas fa-sun"></i> 今日は晴れで暑くなりそうです。水分補給を忘れずに、日焼け対策もしっかりしましょう。熱中症にご注意ください。'
        else:
            return '<i class="fas fa-sun"></i> 今日は晴れの良い天気です。気持ちの良い一日になりそうですね！'
    
    # その他
    else:
        return '今日も一日お疲れ様です。体調に気をつけて過ごしましょう。'