from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

# Auth Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

# Chat Settings Schemas
class ChatSettingsBase(BaseModel):
    # Captcha
    captcha_enabled: bool = True
    captcha_type: str = "button"  # 'button', 'math', 'math_advanced', 'emoji', 'question', 'category', 'compare', 'shapes', 'sequence', 'custom_question', 'random'
    captcha_enabled_types: str = "button,math,math_advanced,emoji,question,category,compare,shapes,sequence"
    custom_captcha_question: Optional[str] = None
    custom_captcha_answer: Optional[str] = None
    captcha_timeout: int = 120
    captcha_fail_action: str = "kick"
    welcome_message_enabled: bool = True
    welcome_text: str = "Добро пожаловать в чат! Пожалуйста, ознакомьтесь с правилами."

    # Filters
    filter_links: bool = True
    whitelisted_domains: str = "t.me,telegram.me,telegram.dog"
    filter_gifs: bool = False
    filter_stickers: bool = False
    filter_voice: bool = False
    filter_video_notes: bool = False
    filter_audio: bool = False
    filter_video: bool = False
    filter_documents: bool = False
    filter_anti_channel: bool = True
    filter_anti_forward: bool = False

    # Flood & Warns
    anti_flood_enabled: bool = True
    anti_flood_max_messages: int = 5
    anti_flood_window_seconds: int = 3
    anti_flood_mute_duration_minutes: int = 10

    max_warns: int = 3
    warns_punishment: str = "mute"
    warns_mute_duration_minutes: int = 60
    warn_expire_hours: int = 24  # 0 = disabled, default 24 hours

    # Protection & Limits
    anti_caps_enabled: bool = False
    anti_caps_threshold_percent: int = 70
    duplicate_spam_enabled: bool = True
    mass_mentions_enabled: bool = True
    mass_mentions_max_count: int = 3
    anti_raid_enabled: bool = False
    anti_raid_joins_per_minute: int = 10

    # Auto Clean & Extras
    bot_auto_delete_seconds: int = 30
    clean_service_messages: bool = True

class ChatSettingsUpdate(ChatSettingsBase):
    pass

class ChatSettingsResponse(ChatSettingsBase):
    chat_id: int
    model_config = ConfigDict(from_attributes=True)

# Chat Schemas
class ChatResponse(BaseModel):
    id: int
    title: str
    username: Optional[str] = None
    type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    settings: Optional[ChatSettingsResponse] = None
    model_config = ConfigDict(from_attributes=True)

# StopWord Schemas
class StopWordCreate(BaseModel):
    word: str
    is_regex: bool = False

class StopWordResponse(BaseModel):
    id: int
    chat_id: int
    word: str
    is_regex: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    chat_id: int
    user_id: Optional[int] = None
    user_fullname: Optional[str] = None
    action: str
    reason: str
    details: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# User Schemas
class WarnResponse(BaseModel):
    id: int
    chat_id: int
    user_id: int
    reason: str
    issuer: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: int
    chat_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool
    is_restricted: bool
    restricted_until: Optional[datetime] = None
    is_banned: bool
    joined_at: datetime
    warns_count: int = 0
    warns: List[WarnResponse] = []
    model_config = ConfigDict(from_attributes=True)

# Dashboard Stats Schemas
class DashboardStatsResponse(BaseModel):
    total_chats: int
    total_users: int
    total_banned_users: int
    total_warns: int
    logs_24h: int
    logs_7d: int
    actions_chart: List[dict]
    activity_chart: List[dict]
