import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    uid = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, unique=True)
    fio = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    group_number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    points = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, default=0)
    login = sqlalchemy.Column(sqlalchemy.String, nullable=True, unique=True)
    admin = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)
    def __repr__(self):
        return f"{self.fio}, {self.uid}, {self.group_number}, {self.points}, {self.admin}"

class Shop(SqlAlchemyBase):
    __tablename__ = "items"
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    discr = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    price = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    def __repr__(self):
        return f"{self.name}, {self.discr}, {self.price}"
