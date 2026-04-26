from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.base import Base


class Edge(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brainmap_id = Column(String(64), nullable=False, index=True)
    
    # 连接节点
    source_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    
    # 关系属性
    relation_type = Column(String(50), nullable=False, default="related")  # parent-child, related, causal, sequential, etc.
    label = Column(String(255), nullable=True)
    weight = Column(Float, nullable=False, default=1.0)  # 边的权重/强度
    directed = Column(Integer, nullable=False, default=1)  # 1=有向, 0=无向
    
    # 3D 可视化属性
    color = Column(String(20), nullable=True, default="#94A3B8")
    width = Column(Float, nullable=False, default=1.0)
    style = Column(String(20), nullable=True, default="solid")  # solid, dashed, dotted
    
    # 路径控制点（支持3D曲线边）
    control_points = Column(JSON, nullable=True, default=list)  # [{"x": 1, "y": 2, "z": 3}, ...]
    
    # 扩展属性
    metadata_json = Column(JSON, nullable=True, default=dict)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    source = relationship("Node", foreign_keys=[source_id], back_populates="outgoing_edges")
    target = relationship("Node", foreign_keys=[target_id], back_populates="incoming_edges")
    
    __table_args__ = (
        Index("idx_edge_brainmap", "brainmap_id"),
        Index("idx_edge_source_target", "source_id", "target_id"),
    )
    
    def __repr__(self):
        return f"<Edge(id={self.id}, {self.source_id}->{self.target_id}, type='{self.relation_type}')>"
