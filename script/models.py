from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

class Companies(Base):

    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, index=True)
    HRname = Column(String)
    email = Column(String, unique=True)
    company = Column(String)

    email_sent = Column(Boolean, default=False)
    