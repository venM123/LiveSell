from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

#-------------------Users-----------------------------#
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    business_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

#----------Live sessions --------------------------#
class LiveSession(Base):
    __tablename__ = "live_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, default="Live Session")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)


#-------------------Orders-----------------------------#

class Order(Base):
    __tablename__ ="orders"
    id = Column(Integer, primary_key=True, index=True)
    
    customer_name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")

    session_id = Column(Integer, ForeignKey("live_sessions.id"), nullable=False)
    session = relationship("LiveSession")


    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product")

    qty = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=True, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
#---------------Products--------------#
class Product(Base):
    __tablename__="products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")
    price = Column(Float, nullable=False, default=0)
    stock = Column(Integer, nullable=False, default=0)
    image_path = Column(String, nullable=True)

#--------------------Password -------------------------#
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

#-----------Database ----------#
DATABASE_URL = "sqlite:///./livesell.db"
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)




def init_db():
    Base.metadata.create_all(bind=engine)
