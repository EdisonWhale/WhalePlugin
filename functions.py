# functions.py
import requests
from common.log import logger
import datetime
from datetime import timedelta
from urllib.parse import urlparse
from bridge.reply import Reply, ReplyType

BASE_URL_VVHAN = "https://api.vvhan.com/api/"
BASE_URL_ALAPI = "https://v2.alapi.cn/api/"

# 获取帮助信息


# 创建回复
def create_reply(reply_type, content):
    reply = Reply()
    reply.type = reply_type
    reply.content = content
    return reply

# 错误处理


def handle_error(error, message):
    logger.error(f"{message}，错误信息：{error}")
    return message

# URL 验证


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# 视频 URL 验证


def is_valid_image_url(url):
    try:
        # Using HEAD request to check the URL header
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException as e:
        return False

# 加载城市信息


def load_city_conditions(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            condition_2_and_3_cities = json.load(f)
        return condition_2_and_3_cities
    except Exception as e:
        return handle_error(e, "加载condition_2_and_3_cities.json失败")

# 检查多个城市 ID


def check_multiple_city_ids(city, condition_2_and_3_cities):
    city_info = condition_2_and_3_cities.get(city)
    if city_info:
        return city_info
    return None  # Changed from whalePlugin to None for a more generic approach


hot_trend_types = {
    "微博": "wbHot",
    "虎扑": "huPu",
    "知乎": "zhihuHot",
    "知乎日报": "zhihuDay",
    "哔哩哔哩": "bili",
    "36氪": "36Ke",
    "抖音": "douyinHot",
    "IT": "itNews",
    "虎嗅": "huXiu",
    "产品经理": "woShiPm",
    "头条": "toutiao",
    "百度": "baiduRD",
    "豆瓣": "douban",
}

# 获取帮助信息


def get_help_text(verbose=False, **kwargs):
    short_help_text = "发送特定指令以获取早报、热榜、查询天气、星座运势、快递信息等！"

    if not verbose:
        return short_help_text

    help_text = "📚 发送关键词获取特定信息！\n"

    # 娱乐和信息类
    help_text += "\n🎉 娱乐与资讯：\n"
    help_text += "  🌅 早报: 发送“早报”获取早报。\n"
    help_text += "  🐟 摸鱼: 发送“摸鱼”获取摸鱼人日历。\n"
    help_text += "  🔥 热榜: 发送“xx热榜”查看支持的热榜。\n"
    help_text += "  🔥 八卦: 发送“八卦”获取明星八卦。\n"

    # 查询类
    help_text += "\n🔍 查询工具：\n"
    help_text += "  🌦️ 天气: 发送“城市+天气”查天气，如“北京天气”。\n"
    help_text += "  📦 快递: 发送“快递+单号”查询快递状态。如“快递112345655”\n"
    help_text += "  🌌 星座: 发送星座名称查看今日运势，如“白羊座”。\n"

    return help_text


# 获取早报信息
def get_morning_news(alapi_token, morning_news_text_enabled, make_request, handle_error, BASE_URL_VVHAN, BASE_URL_ALAPI):
    if not alapi_token:
        url = BASE_URL_VVHAN + "60s?type=json"
        payload = "format=json"
        headers = {'Content-Type': "application/x-www-form-urlencoded"}

        # 从vvhan获取早报信息
        try:
            morning_news_info = make_request(
                url, method="POST", headers=headers, data=payload)
            if isinstance(morning_news_info, dict) and morning_news_info['success']:
                if morning_news_text_enabled:
                    news_list = ["{}. {}".format(idx, news) for idx, news in enumerate(
                        morning_news_info["data"][:-1], 1)]
                    formatted_news = f"☕ {morning_news_info['data']['date']}  今日早报\n" + "\n".join(
                        news_list)
                    weiyu = morning_news_info["data"][-1].strip()
                    return f"{formatted_news}\n\n{weiyu}\n\n 图片url：{morning_news_info['imgUrl']}"
                else:
                    return morning_news_info['imgUrl']
            else:
                return handle_error(morning_news_info, '早报信息获取失败，可配置"alapi token"切换至 Alapi 服务，或者稍后再试')
        except Exception as e:
            return handle_error(e, "出错啦，稍后再试")
    else:
        url = BASE_URL_ALAPI + "zaobao"
        data = {
            "token": alapi_token,
            "format": "json"
        }
        headers = {'Content-Type': "application/x-www-form-urlencoded"}

        # 从alapi获取早报信息
        try:
            morning_news_info = make_request(
                url, method="POST", headers=headers, data=data)
            if isinstance(morning_news_info, dict) and morning_news_info.get('code') == 200:
                img_url = morning_news_info['data']['image']
                if morning_news_text_enabled:
                    news_list = morning_news_info['data']['news']
                    weiyu = morning_news_info['data']['weiyu']
                    formatted_news = f"☕ {morning_news_info['data']['date']}  今日早报\n" + "\n".join(
                        news_list)
                    return f"{formatted_news}\n\n{weiyu}\n\n 图片url：{img_url}"
                else:
                    return img_url
            else:
                return handle_error(morning_news_info, "早报获取失败，请检查 token 是否有误")
        except Exception as e:
            return handle_error(e, "早报获取失败")


# 获取摸鱼日历信息
def get_moyu_calendar(make_request, is_valid_image_url, BASE_URL_VVHAN):
    # 尝试从vvhan获取摸鱼日历信息
    url = BASE_URL_VVHAN + "moyu?type=json"
    payload = "format=json"
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    moyu_calendar_info = make_request(
        url, method="POST", headers=headers, data=payload)

    # 验证第一个URL请求是否成功
    if isinstance(moyu_calendar_info, dict) and moyu_calendar_info['success']:
        return moyu_calendar_info['url']
    else:
        # 第一个URL失败，尝试第二个备用URL
        url = "https://dayu.qqsuu.cn/moyuribao/apis.php?type=json"
        moyu_calendar_info = make_request(
            url, method="POST", headers=headers, data=payload)

        # 验证第二个URL请求是否成功
        if isinstance(moyu_calendar_info, dict) and moyu_calendar_info['code'] == 200:
            moyu_pic_url = moyu_calendar_info['data']
            # 检查图片URL是否有效
            if is_valid_image_url(moyu_pic_url):
                return moyu_pic_url
            else:
                # 图片URL无效时的备用消息
                return "周末无需摸鱼，愉快玩耍吧"
        else:
            # 两个URL都失败时的备用消息
            return "暂无可用“摸鱼”服务，认真上班"

# 获取摸鱼日历视频


def get_moyu_calendar_video(make_request, is_valid_image_url, logger):
    url = "https://dayu.qqsuu.cn/moyuribaoshipin/apis.php?type=json"
    payload = "format=json"
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    moyu_calendar_info = make_request(
        url, method="POST", headers=headers, data=payload)
    logger.debug(
        f"[whalePlugin] moyu calendar video response: {moyu_calendar_info}")

    # 验证请求是否成功
    if isinstance(moyu_calendar_info, dict) and moyu_calendar_info['code'] == 200:
        moyu_video_url = moyu_calendar_info['data']
        if is_valid_image_url(moyu_video_url):  # 注意这里可能需要改为 `is_valid_video_url`
            return moyu_video_url

    # 未成功请求到视频时，返回提示信息
    return "视频版没了，看看文字版吧"

# 获取星座运势


def get_horoscope(make_request, handle_error, BASE_URL_VVHAN, BASE_URL_ALAPI, alapi_token, astro_sign, time_period="today"):
    if not alapi_token:
        url = BASE_URL_VVHAN + "horoscope"
        params = {
            'type': astro_sign,
            'time': time_period
        }
        try:
            horoscope_data = make_request(url, "GET", params=params)
            if isinstance(horoscope_data, dict) and horoscope_data['success']:
                # 省略了具体的数据处理和格式化...
                data = horoscope_data['data']
                result = result = (
                    f"{data['title']} ({data['time']}):\n\n"
                    f"💡【每日建议】\n宜：{data['todo']['yi']}\n忌：{data['todo']['ji']}\n\n"
                    f"📊【运势指数】\n"
                    f"总运势：{data['index']['all']}\n"
                    f"爱情：{data['index']['love']}\n"
                    f"工作：{data['index']['work']}\n"
                    f"财运：{data['index']['money']}\n"
                    f"健康：{data['index']['health']}\n\n"
                    f"🍀【幸运提示】\n数字：{data['luckynumber']}\n"
                    f"颜色：{data['luckycolor']}\n"
                    f"星座：{data['luckyconstellation']}\n\n"
                    f"✍【简评】\n{data['shortcomment']}\n\n"
                    f"📜【详细运势】\n"
                    f"总运：{data['fortunetext']['all']}\n"
                    f"爱情：{data['fortunetext']['love']}\n"
                    f"工作：{data['fortunetext']['work']}\n"
                    f"财运：{data['fortunetext']['money']}\n"
                    f"健康：{data['fortunetext']['health']}\n"
                )
                return result
            else:
                return handle_error(horoscope_data, '星座信息获取失败，可配置"alapi token"切换至 Alapi 服务，或者稍后再试')
        except Exception as e:
            return handle_error(e, "出错啦，稍后再试")
    else:
        # 使用 ALAPI 的 URL 和提供的 token
        url = BASE_URL_ALAPI + "star"
        payload = f"token={alapi_token}&star={astro_sign}"
        headers = {'Content-Type': "application/x-www-form-urlencoded"}
        try:
            horoscope_data = make_request(
                url, method="POST", headers=headers, data=payload)
            if isinstance(horoscope_data, dict) and horoscope_data.get('code') == 200:
                # 省略了具体的数据处理和格式化...
                result = (
                    f"📅 日期：{data['date']}\n\n"
                    f"💡【每日建议】\n宜：{data['yi']}\n忌：{data['ji']}\n\n"
                    f"📊【运势指数】\n"
                    f"总运势：{data['all']}\n"
                    f"爱情：{data['love']}\n"
                    f"工作：{data['work']}\n"
                    f"财运：{data['money']}\n"
                    f"健康：{data['health']}\n\n"
                    f"🔔【提醒】：{data['notice']}\n\n"
                    f"🍀【幸运提示】\n数字：{data['lucky_number']}\n"
                    f"颜色：{data['lucky_color']}\n"
                    f"星座：{data['lucky_star']}\n\n"
                    f"✍【简评】\n总运：{data['all_text']}\n"
                    f"爱情：{data['love_text']}\n"
                    f"工作：{data['work_text']}\n"
                    f"财运：{data['money_text']}\n"
                    f"健康：{data['health_text']}\n"
                )
                return result
            else:
                return handle_error(horoscope_data, "星座获取信息获取失败，请检查 token 是否有误")
        except Exception as e:
            return handle_error(e, "出错啦，稍后再试")


# 获取热榜信息
def get_hot_trends(make_request, handle_error, BASE_URL_VVHAN, hot_trend_types, whalePlugin, hot_trends_type):
    # 查找映射字典以获取API参数
    hot_trends_type_en = hot_trend_types.get(hot_trends_type, whalePlugin)
    if hot_trends_type_en is not whalePlugin:
        url = BASE_URL_VVHAN + "hotlist/" + hot_trends_type_en
        try:
            data = make_request(url, "GET", headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            if isinstance(data, dict) and data['success']:
                output = []
                topics = data['data']
                output.append(f'更新时间：{data["update_time"]}\n')
                for i, topic in enumerate(topics[:15], 1):
                    hot = topic.get('hot', '无热度参数, 0')
                    formatted_str = f"{i}. {topic['title']} ({hot} 浏览)\nURL: {topic['url']}\n"
                    output.append(formatted_str)
                return "\n".join(output)
            else:
                return handle_error(data, "热榜获取失败，请稍后再试")
        except Exception as e:
            return handle_error(e, "出错啦，稍后再试")
    else:
        supported_types = "/".join(hot_trend_types.keys())
        final_output = (
            f"👉 已支持的类型有：\n\n    {supported_types}\n"
            f"\n📝 请按照以下格式发送：\n    类型+热榜  例如：微博热榜"
        )
        return final_output


def get_weather(alapi_token, city_or_id: str, date: str, content):
    # 根据日期确定 API 端点
    url = BASE_URL_ALAPI + \
        ('tianqi' if date not in ['明天', '后天', '七天', '7天'] else 'tianqi/seven')

    # 确定 city_or_id 是城市 ID 还是城市名称
    if city_or_id.isnumeric():
        params = {'city_id': city_or_id, 'token': alapi_token}
    else:
        city_info = check_multiple_city_ids(city_or_id)
        if city_info:
            # 如果找到多个城市 ID，提示用户使用 ID 进行查询
            data = city_info['data']
            formatted_city_info = "\n".join(
                [f"{idx + 1}) {entry['province']}--{entry['leader']}, ID: {entry['city_id']}" for idx, entry in enumerate(data)])
            return f"找到 <{city_or_id}> 多个数据：\n{formatted_city_info}\n请使用 ID 进行查询，发送 'id+天气'"

        params = {'city': city_or_id, 'token': alapi_token}

    try:
        # 发起 API 请求
        weather_data = make_request(url, "GET", params=params)

        if isinstance(weather_data, dict) and weather_data.get('code') == 200:
            data = weather_data['data']

            # 处理未来天气数据
            if date in ['明天', '后天', '七天', '7天']:
                formatted_output = process_future_weather(data, date)
                return "\n".join(formatted_output)

            # 处理当前天气数据
            formatted_output = process_current_weather(
                data, content, city_or_id)
            return "\n".join(formatted_output)
    except Exception as e:
        return f"发生错误：{e}"


def process_future_weather(data, date):
    # 处理和格式化未来天气数据
    formatted_output = []
    for num, d in enumerate(data):
        if num == 0:
            formatted_output.append(f"🏙️ 城市: {d['city']} ({d['province']})\n")
        if date == '明天' and num != 1:
            continue
        if date == '后天' and num != 2:
            continue
        basic_info = [
            f"🕒 日期: {d['date']}",
            f"🌦️ 天气: 🌞{d['wea_day']}| 🌛{d['wea_night']}",
            f"🌡️ 温度: 🌞{d['temp_day']}℃| 🌛{d['temp_night']}℃",
            f"🌅 日出/日落: {d['sunrise']} / {d['sunset']}",
        ]
        for i in d['index']:
            basic_info.append(f"{i['name']}: {i['level']}")
        formatted_output.append("\n".join(basic_info) + '\n')
    return formatted_output


def make_request(url, method="GET", headers=None, params=None, data=None, json_data=None):
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(
                url, headers=headers, data=data, json=json_data)
        else:
            return {"success": False, "message": "不支持的 HTTP 方法"}

        return response.json()
    except Exception as e:
        return e


def process_current_weather(data, content, city_or_id):
    # 处理和格式化当前天气数据
    formatted_output = []
    update_time = datetime.strptime(
        data['update_time'], "%Y-%m-%d %H:%M:%S").strftime("%m-%d %H:%M")

    if not city_or_id.isnumeric() and data['city'] not in content:
        return "输入格式不正确。请输入<城市+(今天|明天|后天|七天)+天气>，例如 '广州天气'"

    basic_info = (
        f"🏙️ 城市: {data['city']} ({data['province']})\n"
        f"🕒 更新: {update_time}\n"
        f"🌦️ 天气: {data['weather']}\n"
        f"🌡️ 温度: ↓{data['min_temp']}℃| 现{data['temp']}℃| ↑{data['max_temp']}℃\n"
        f"🌬️ 风向: {data['wind']}\n"
        f"💦 湿度: {data['humidity']}\n"
        f"🌅 日出/日落: {data['sunrise']} / {data['sunset']}\n"
    )
    formatted_output.append(basic_info)

    chuangyi_data = data.get('index', {}).get('chuangyi', {})
    chuangyi_level = chuangyi_data.get(
        'level', '未知') if chuangyi_data else '未知'
    chuangyi_content = chuangyi_data.get(
        'content', '未知') if chuangyi_data else '未知'
    chuangyi_info = f"👚 穿衣指数: {chuangyi_level} - {chuangyi_content}\n"
    formatted_output.append(chuangyi_info)

    ten_hours_later = datetime.strptime(
        data['update_time'], "%Y-%m-%d %H:%M:%S") + timedelta(hours=10)
    future_weather = []
    for hour_data in data['hour']:
        forecast_time = datetime.strptime(
            hour_data['time'], "%Y-%m-%d %H:%M:%S")
        if datetime.strptime(data['update_time'], "%Y-%m-%d %H:%M:%S") < forecast_time <= ten_hours_later:
            future_weather.append(
                f"     {forecast_time.hour:02d}:00 - {hour_data['wea']} - {hour_data['temp']}°C")
    future_weather_info = "⏳ 未来10小时的天气预报:\n" + "\n".join(future_weather)
    formatted_output.append(future_weather_info)

    if data.get('alarm'):
        alarm_info = "⚠️ 预警信息:\n"
        for alarm in data['alarm']:
            alarm_info += (
                f"🔴 标题: {alarm['title']}\n"
                f"🟠 等级: {alarm['level']}\n"
                f"🟡 类型: {alarm['type']}\n"
                f"🟢 提示: \n{alarm['tips']}\n"
                f"🔵 内容: \n{alarm['content']}\n\n"
            )
        formatted_output.append(alarm_info)

    return formatted_output

# 获取八卦信息


def get_mx_bagua(make_request, is_valid_image_url):
    url = "https://dayu.qqsuu.cn/mingxingbagua/apis.php?type=json"
    payload = "format=json"
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    bagua_info = make_request(
        url, method="POST", headers=headers, data=payload)
    # Validate request success
    if isinstance(bagua_info, dict) and bagua_info['code'] == 200:
        bagua_pic_url = bagua_info["data"]
        if is_valid_image_url(bagua_pic_url):
            return bagua_pic_url
        else:
            return "周末不更新，请微博吃瓜"
    else:
        logger.error(f"错误信息：{bagua_info}")
        return "暂无明星八卦，吃瓜莫急"

# 获取每日一题


def fetch_daily_question():
    base_url = 'https://leetcode.com/graphql'
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'
    }
    query = """
    query questionOfToday {
        activeDailyCodingChallengeQuestion {
            date
            question {
                title
                titleSlug
                questionFrontendId
            }
        }
    }
    """
    # 发起请求
    response = requests.post(base_url, json={'query': query}, headers=headers)
    if response.status_code == 200:
        try:
            data = response.json()
            question = data['data']['activeDailyCodingChallengeQuestion']['question']
            title = f"{question['questionFrontendId']}. {question['title']}"
            title_slug = question['titleSlug']
            url = f"https://leetcode.com/problems/{title_slug}"
            return title, url
        except KeyError as e:
            print(f"Error parsing response JSON: {e}")
            return None, None
    else:
        print(f"Failed to fetch daily question: {response.status_code}")
        return None, None
