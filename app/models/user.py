from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.config.database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    
    # relationship 추가
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    
    # 연락처 관계 설정
    contacts = relationship("Contact", foreign_keys="Contact.user_id", back_populates="user")
    contacted_by = relationship("Contact", foreign_keys="Contact.contact_id", back_populates="contact")