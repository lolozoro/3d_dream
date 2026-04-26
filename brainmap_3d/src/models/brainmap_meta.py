from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from src.db.base import Base


class BrainMapMeta(Base):
    """脑图元数据表，用于存储脑图列表信息"""
    __tablename__ = "brainmap_meta"

    brainmap_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<BrainMapMeta(id='{self.brainmap_id}', title='{self.title}')>"
