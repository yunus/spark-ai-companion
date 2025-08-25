"""
This module defines the DeclarativeBase for all SQLAlchemy ORM models.
All table models in the application should inherit from this Base class.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """The base class for all SQLAlchemy ORM models."""

    pass


__all__ = [Base]
