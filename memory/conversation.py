"""
记忆模块
对话记忆与用户画像管理
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json
import os


class Message(BaseModel):
    """消息模型"""
    role: str  # user / assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMemory(BaseModel):
    """对话记忆"""
    session_id: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加消息"""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata or {}
        ))
        self.updated_at = datetime.now()
    
    def get_context(self, max_messages: int = 10) -> str:
        """获取上下文"""
        recent_messages = self.messages[-max_messages:]
        context_parts = []
        for msg in recent_messages:
            role_label = "用户" if msg.role == "user" else "助手"
            context_parts.append(f"{role_label}: {msg.content}")
        return "\n".join(context_parts)
    
    def clear(self) -> None:
        """清空记忆"""
        self.messages.clear()
        self.updated_at = datetime.now()


class ConversationManager:
    """对话管理器"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "conversations"
        )
        self._sessions: Dict[str, ConversationMemory] = {}
    
    def get_or_create_session(self, session_id: str) -> ConversationMemory:
        """获取或创建会话"""
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationMemory(session_id=session_id)
        return self._sessions[session_id]
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """添加消息到会话"""
        session = self.get_or_create_session(session_id)
        session.add_message(role, content, metadata)
    
    def get_session(self, session_id: str) -> Optional[ConversationMemory]:
        """获取会话"""
        return self._sessions.get(session_id)
    
    def clear_session(self, session_id: str) -> None:
        """清空会话"""
        if session_id in self._sessions:
            self._sessions[session_id].clear()
    
    def save_session(self, session_id: str) -> None:
        """保存会话到文件"""
        if session_id not in self._sessions:
            return
        
        os.makedirs(self.storage_path, exist_ok=True)
        filepath = os.path.join(self.storage_path, f"{session_id}.json")
        
        session = self._sessions[session_id]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def load_session(self, session_id: str) -> Optional[ConversationMemory]:
        """从文件加载会话"""
        filepath = os.path.join(self.storage_path, f"{session_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            session = ConversationMemory(**data)
            self._sessions[session_id] = session
            return session
            
        except Exception as e:
            return None


class RiskPreference(BaseModel):
    """风险偏好"""
    level: str = "moderate"  # conservative/moderate/aggressive
    max_position: float = 0.3
    stop_loss: float = -0.08
    take_profit: float = 0.15


class UserProfile(BaseModel):
    """用户画像"""
    user_id: str
    nickname: Optional[str] = None
    
    # 风险偏好
    risk_preference: RiskPreference = Field(default_factory=RiskPreference)
    
    # 自选股
    watchlist: List[str] = Field(default_factory=list)
    
    # 偏好行业
    preferred_sectors: List[str] = Field(default_factory=list)
    
    # 交互历史
    query_count: int = 0
    last_active: datetime = Field(default_factory=datetime.now)
    
    # 标签
    tags: List[str] = Field(default_factory=list)


class UserProfileManager:
    """用户画像管理器"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "profiles"
        )
        self._profiles: Dict[str, UserProfile] = {}
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """获取或创建用户画像"""
        if user_id not in self._profiles:
            # 尝试从文件加载
            profile = self.load_profile(user_id)
            if profile:
                self._profiles[user_id] = profile
            else:
                self._profiles[user_id] = UserProfile(user_id=user_id)
        return self._profiles[user_id]
    
    def update_risk_preference(
        self,
        user_id: str,
        level: str = None,
        max_position: float = None,
        stop_loss: float = None,
        take_profit: float = None
    ) -> None:
        """更新风险偏好"""
        profile = self.get_or_create_profile(user_id)
        
        if level:
            profile.risk_preference.level = level
        if max_position is not None:
            profile.risk_preference.max_position = max_position
        if stop_loss is not None:
            profile.risk_preference.stop_loss = stop_loss
        if take_profit is not None:
            profile.risk_preference.take_profit = take_profit
        
        profile.last_active = datetime.now()
    
    def add_to_watchlist(self, user_id: str, stock_code: str) -> None:
        """添加自选股"""
        profile = self.get_or_create_profile(user_id)
        if stock_code not in profile.watchlist:
            profile.watchlist.append(stock_code)
        profile.last_active = datetime.now()
    
    def remove_from_watchlist(self, user_id: str, stock_code: str) -> None:
        """移除自选股"""
        profile = self.get_or_create_profile(user_id)
        if stock_code in profile.watchlist:
            profile.watchlist.remove(stock_code)
        profile.last_active = datetime.now()
    
    def increment_query_count(self, user_id: str) -> None:
        """增加查询次数"""
        profile = self.get_or_create_profile(user_id)
        profile.query_count += 1
        profile.last_active = datetime.now()
    
    def save_profile(self, user_id: str) -> None:
        """保存用户画像到文件"""
        if user_id not in self._profiles:
            return
        
        os.makedirs(self.storage_path, exist_ok=True)
        filepath = os.path.join(self.storage_path, f"{user_id}.json")
        
        profile = self._profiles[user_id]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        """从文件加载用户画像"""
        filepath = os.path.join(self.storage_path, f"{user_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return UserProfile(**data)
        except Exception as e:
            return None
