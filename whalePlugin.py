import plugins
import requests
import re
import json
from urllib.parse import urlparse
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel import channel
from common.log import logger
from plugins import *
from datetime import datetime, timedelta
from functions import *


@plugins.register(
    name="whalePlugin",
    desire_priority=88,
    hidden=False,
    desc="A plugin to handle specific keywords",
    version="0.15",
    author="vision",
)
class whalePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.alapi_token = None
        self.morning_news_text_enabled = False
        try:
            self.conf = super().load_config()
            if not self.conf:
                logger.warn(
                    "[whalePlugin] Initialized but 'alapi_token' not found in config.")
            else:
                logger.info(
                    "[whalePlugin] Initialized and 'alapi_token' loaded successfully.")
                self.alapi_token = self.conf.get("alapi_token")
                self.morning_news_text_enabled = self.conf.get(
                    "morning_news_text_enabled", False)
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            handle_error(e, "[whalePlugin] Initialization failed, ignoring.")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return
        content = e_context["context"].content.strip()
        logger.debug(f"[whalePlugin] on_handle_context. Content: {content}")

        # 早报功能
        if content == "早报":
            news = get_morning_news(
                self.alapi_token, self.morning_news_text_enabled)
            reply_type = ReplyType.IMAGE_URL if is_valid_url(
                news) else ReplyType.TEXT
            reply = create_reply(reply_type, news)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        # 摸鱼日历功能
        if content == "摸鱼":
            moyu = get_moyu_calendar()
            reply_type = ReplyType.IMAGE_URL if is_valid_url(
                moyu) else ReplyType.TEXT
            reply = create_reply(reply_type, moyu)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        # 每日一题功能
        if content == "每日一题":
            title, url = fetch_daily_question()
            if title and url:
                reply_content = f"今天的每日一题是：{title}\n题目链接：{url}"
            else:
                reply_content = "无法获取每日一题，请稍后再试。"
            reply = create_reply(ReplyType.TEXT, reply_content)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        # 摸鱼视频功能
        if content == "摸鱼视频":
            moyu_video = get_moyu_calendar_video()
            reply_type = ReplyType.VIDEO_URL if is_valid_url(
                moyu_video) else ReplyType.TEXT
            reply = create_reply(reply_type, moyu_video)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        # 八卦功能
        if content == "八卦":
            bagua = get_mx_bagua()
            reply_type = ReplyType.IMAGE_URL if is_valid_url(
                bagua) else ReplyType.TEXT
            reply = create_reply(reply_type, bagua)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        # 星座运势功能
        horoscope_match = re.match(r'^([\u4e00-\u9fa5]{2}座)$', content)
        if horoscope_match:
            if content in ZODIAC_MAPPING:
                zodiac_english = ZODIAC_MAPPING[content]
                horoscope_info = get_horoscope(
                    self.alapi_token, zodiac_english)
                reply = create_reply(ReplyType.TEXT, horoscope_info)
            else:
                reply = create_reply(ReplyType.TEXT, "请重新输入星座名称")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        # 热榜功能
        hot_trend_match = re.search(r'(.{1,6})热榜$', content)
        if hot_trend_match:
            hot_trends_type = hot_trend_match.group(1).strip()
            hot_trends_info = get_hot_trends(hot_trends_type)
            reply = create_reply(ReplyType.TEXT, hot_trends_info)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        # 天气查询功能
        weather_match = re.match(
            r'^(?:(.{2,7}?)(?:市|县|区|镇)?|(\d{7,9}))(:?今天|明天|后天|7天|七天)?(?:的)?天气$', content)
        if weather_match:
            city_or_id = weather_match.group(1) or weather_match.group(2)
            date = weather_match.group(3) or "今天"
            if not self.alapi_token:
                handle_error("alapi_token not configured",
                             "Weather request failed.")
                reply = create_reply(
                    ReplyType.TEXT, "Please configure the 'alapi_token' first.")
            else:
                weather_info = get_weather(self.alapi_token, city_or_id, date)
                reply = create_reply(ReplyType.TEXT, weather_info)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return


ZODIAC_MAPPING = {
    '白羊座': 'aries',
    '金牛座': 'taurus',
    '双子座': 'gemini',
    '巨蟹座': 'cancer',
    '狮子座': 'leo',
    '处女座': 'virgo',
    '天秤座': 'libra',
    '天蝎座': 'scorpio',
    '射手座': 'sagittarius',
    '摩羯座': 'capricorn',
    '水瓶座': 'aquarius',
    '双鱼座': 'pisces'
}
