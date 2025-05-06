from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.config.database import Base
from datetime import datetime

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 관계 설정
    user = relationship("User", foreign_keys=[user_id], back_populates="contacts")
    contact = relationship("User", foreign_keys=[contact_id], back_populates="contacted_by") 