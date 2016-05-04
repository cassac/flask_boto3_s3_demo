from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class Image(Base):
    __tablename__ = 'image'
    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    filename = Column(String(50))
    url = Column(String(120), unique=True)
    thumb_url = Column(String(120), unique=True)

    def __init__(self, title, filename, url, thumb_url):
        self.title = title
        self.filename = filename
        self.url = url
        self.thumb_url = thumb_url

    def __repr__(self):
        return '<Image %r>' % (self.filename)