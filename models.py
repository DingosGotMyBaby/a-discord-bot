from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Classes
class User(Base):
    """
    Model for the users table

    Args:
        Base (Base): Declared base from SQLAlchemy
        userid (BigInteger): Primary key for the table, Discord User ID
        username (String): Discord Username
        pronouns (String): User's pronouns, if they choose to share

    Returns:
        User: SQLAlchemy model for the users table
    """    
    __tablename__ = "users"
    userid = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    pronouns = Column(String, default=None, nullable=True)

    # Define a one-to-many relationship with the Rolls model
    rolls = relationship("Rolls", back_populates="user", foreign_keys="Rolls.user_id")
    doublerolls = relationship("DoubleRolls", back_populates="user", foreign_keys="DoubleRolls.user_id")

    def __repr__(self):
        return f"<User(userid={self.userid}, username={self.username}, pronouns={self.pronouns})>"

class Rolls(Base):
    """
    Model for the rolls table
    This table tracks the rolls made by users

    Args:
        Base (Base): Declared base from SQLAlchemy
        roll_id (Integer): Primary key for the table
        user_id (BigInteger): Foreign key to the users table
        roll (Integer): The roll value
        timestamp (DateTime): The time the roll was made
        roll_removed (Boolean): If the roll was removed
        removed_by (BigInteger): Foreign key to the users table denoting who removed the roll

    Returns:
        _type_: _description_
    """    
    __tablename__ = "rolls"
    roll_id = Column(Integer, primary_key=True)  # Correct the primary key name
    user_id = Column(BigInteger, ForeignKey('users.userid'), nullable=False)
    roll = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    roll_removed = Column(Boolean, default=False)
    removed_by = Column(BigInteger, ForeignKey('users.userid'))

    # Define a many-to-one relationship with the User model
    user = relationship("User", back_populates="rolls", foreign_keys=[user_id])
    
    # Define a many-to-one relationship for the removed_by user
    removed_by_user = relationship("User", foreign_keys=[removed_by])

    def __repr__(self):
        return f"<Rolls(roll_id={self.roll_id}, user_id={self.user_id}, roll={self.roll}, timestamp={self.timestamp}, removed={self.roll_removed}, removed_by={self.removed_by})>"
    
class DoubleRolls(Base):
    """
    Model for the doublerolls table
    This table tracks when a user rolls multiple times in a day

    Args:
        Base (Base): Declared base from SQLAlchemy
        doubleroll_id (Integer): Primary key for the table
        user_id (BigInteger): Foreign key to the users table
        timestamp (DateTime): The time the roll was made

    Returns:
        _type_: _description_
    """    
    __tablename__ = "doublerolls"
    doubleroll_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.userid'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    # Define a many-to-one relationship with the User model
    user = relationship("User", back_populates="doublerolls", foreign_keys=[user_id])
    

    def __repr__(self):
        return f"<DoubleRolls(doubleroll_id={self.doubleroll_id}, user_id={self.user_id}, roll={self.roll}, timestamp={self.timestamp}>"
