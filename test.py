from datetime import datetime

def my_view(request):
    today = datetime.today()
    weekdays = {
        "Monday": "月曜日",
        "Tuesday": "火曜日",
        "Wednesday": "水曜日",
        "Thursday": "木曜日",
        "Friday": "金曜日",
        "Saturday": "土曜日",
        "Sunday": "日曜日"
    }
    
    context = {
        "today": today.strftime("%Y年%m月%d日") + " (" + weekdays[today.strftime("%A")] + ")"
    }
    return render(request, "my_template.html", context)