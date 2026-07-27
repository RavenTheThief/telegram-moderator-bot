from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base

class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)  # Telegram Chat ID
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(50), default="supergroup")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    settings: Mapped["ChatSettings"] = relationship("ChatSettings", back_populates="chat", uselist=False, cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship("User", back_populates="chat", cascade="all, delete-orphan")
    stop_words: Mapped[list["StopWord"]] = relationship("StopWord", back_populates="chat", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="chat", cascade="all, delete-orphan")


class ChatSettings(Base):
    __tablename__ = "chat_settings"

    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)

    # Captcha
    captcha_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    captcha_type: Mapped[str] = mapped_column(String(50), default="button")  # 'button' or 'math'
    captcha_timeout: Mapped[int] = mapped_column(Integer, default=120)  # seconds
    captcha_fail_action: Mapped[str] = mapped_column(String(50), default="kick")  # 'kick' or 'ban'
    welcome_message_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    welcome_text: Mapped[str] = mapped_column(Text, default="Добро пожаловать в чат! Пожалуйста, ознакомьтесь с правилами.")

    # Content Filters
    filter_links: Mapped[bool] = mapped_column(Boolean, default=True)
    whitelisted_domains: Mapped[str] = mapped_column(Text, default="t.me,telegram.me,telegram.dog")
    filter_gifs: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_stickers: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_voice: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_video_notes: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_audio: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_video: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_documents: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_anti_channel: Mapped[bool] = mapped_column(Boolean, default=True)
    filter_anti_forward: Mapped[bool] = mapped_column(Boolean, default=False)

    # Anti-Flood & Warns
    anti_flood_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    anti_flood_max_messages: Mapped[int] = mapped_column(Integer, default=5)
    anti_flood_window_seconds: Mapped[int] = mapped_column(Integer, default=3)
    anti_flood_mute_duration_minutes: Mapped[int] = mapped_column(Integer, default=10)

    max_warns: Mapped[int] = mapped_column(Integer, default=3)
    warns_punishment: Mapped[str] = mapped_column(String(50), default="mute")  # 'mute' or 'ban'
    warns_mute_duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    warn_expire_hours: Mapped[int] = mapped_column(Integer, default=24)  # 0 = disabled, default 24 hours

    # Protection & Limits
    anti_caps_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_caps_threshold_percent: Mapped[int] = mapped_column(Integer, default=70)
    duplicate_spam_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    mass_mentions_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    mass_mentions_max_count: Mapped[int] = mapped_column(Integer, default=3)
    anti_raid_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_raid_joins_per_minute: Mapped[int] = mapped_column(Integer, default=10)

    # Auto Clean & Extras
    bot_auto_delete_seconds: Mapped[int] = mapped_column(Integer, default=30)
    clean_service_messages: Mapped[bool] = mapped_column(Boolean, default=True)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="settings")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram User ID
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False)
    restricted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped["Chat"] = relationship("Chat", back_populates="users")
    warns: Mapped[list["Warn"]] = relationship(
        "Warn",
        primaryjoin="and_(User.id==Warn.user_id, User.chat_id==Warn.chat_id)",
        foreign_keys="[Warn.user_id, Warn.chat_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Warn(Base):
    __tablename__ = "warns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    reason: Mapped[str] = mapped_column(String(255), default="Нарушение правил чата")
    issuer: Mapped[str] = mapped_column(String(100), default="System")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(
        "User",
        primaryjoin="and_(Warn.user_id==User.id, Warn.chat_id==User.chat_id)",
        foreign_keys="[Warn.user_id, Warn.chat_id]",
        back_populates="warns"
    )


class StopWord(Base):
    __tablename__ = "stop_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    is_regex: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped["Chat"] = relationship("Chat", back_populates="stop_words")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_fullname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'delete_message', 'mute_user', 'ban_user'
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped["Chat"] = relationship("Chat", back_populates="audit_logs")
