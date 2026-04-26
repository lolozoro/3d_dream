from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.base import Base


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brainmap_id = Column(String(64), nullable=False, index=True)
    
    # 基础信息
    label = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    node_type = Column(String(50), nullable=False, default="concept")  # concept, topic, detail, image, video, link, etc.
    
    # 3D 坐标
    pos_x = Column(Float, nullable=False, default=0.0)
    pos_y = Column(Float, nullable=False, default=0.0)
    pos_z = Column(Float, nullable=False, default=0.0)
    
    # 3D 可视化属性
    size = Column(Float, nullable=False, default=1.0)
    color = Column(String(20), nullable=True, default="#4F46E5")
    shape = Column(String(20), nullable=True, default="sphere")  # sphere, cube, cone, etc.
    opacity = Column(Float, nullable=False, default=1.0)
    
    # 层级与分组（支持多维组织）
    layer = Column(Integer, nullable=False, default=0)  # 层级深度
    group_id = Column(String(64), nullable=True, index=True)  # 分组ID
    parent_id = Column(Integer, ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True)
    
    # 扩展属性
    metadata_json = Column(JSON, nullable=True, default=dict)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    parent = relationship("Node", remote_side=[id], back_populates="children")
    children = relationship("Node", back_populates="parent")
    outgoing_edges = relationship("Edge", foreign_keys="Edge.source_id", back_populates="source")
    incoming_edges = relationship("Edge", foreign_keys="Edge.target_id", back_populates="target")
    
    __table_args__ = (
        Index("idx_node_brainmap_layer", "brainmap_id", "layer"),
        Index("idx_node_3d_coords", "pos_x", "pos_y", "pos_z"),
    )
    
    def __repr__(self):
        return f"<Node(id={self.id}, label='{self.label}', brainmap='{self.brainmap_id}')>"
