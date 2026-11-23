"""Modelos relacionales multi-tenant para LeadHunter AI SaaS.
Compatible con SQLite y PostgreSQL 16.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    commercial_profile = Column(Text, default="")
    country = Column(String(100), default="")
    city = Column(String(100), default="")
    ideal_customer_profile = Column(Text, default="{}")  # JSON serializado
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="organization", cascade="all, delete-orphan")
    saved_searches = relationship("SavedSearch", back_populates="organization", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="organization", uselist=False, cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="owner")  # owner, admin, member
    joined_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
    )


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(50), primary_key=True)  # starter, growth, enterprise
    name = Column(String(100), nullable=False)
    max_organizations = Column(Integer, default=1)
    monthly_searches = Column(Integer, default=50)
    monthly_leads = Column(Integer, default=500)
    price_usd = Column(Numeric(10, 2), default=0.00)
    is_active = Column(Boolean, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan_id = Column(String(50), ForeignKey("plans.id"), nullable=False)
    provider = Column(String(50), default="manual")  # stripe, lemonsqueezy, manual
    provider_customer_id = Column(String(255), default="")
    provider_subscription_id = Column(String(255), default="")
    status = Column(String(50), default="active")  # active, past_due, canceled
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="subscription")
    plan = relationship("Plan")


class Lead(Base):
    __tablename__ = "leads_v2"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    dedupe_key = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(500), default="")
    phone = Column(String(100), default="")
    email = Column(String(255), default="")
    instagram = Column(String(255), default="")
    country = Column(String(100), default="")
    city = Column(String(100), default="")
    sector = Column(String(100), default="")
    source = Column(String(100), default="")
    address = Column(Text, default="")
    score = Column(Integer, default=0, index=True)
    score_detail = Column(Text, default="{}")  # JSON
    evidence = Column(Text, default="[]")      # JSON
    inferences = Column(Text, default="[]")    # JSON
    status = Column(String(50), default="Nuevo", index=True)
    notes = Column(Text, default="")
    next_followup = Column(String(50), default="")
    analyzed = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="leads")

    __table_args__ = (
        UniqueConstraint("organization_id", "dedupe_key", name="uq_org_lead_dedupe"),
    )


class SavedSearch(Base):
    __tablename__ = "saved_searches_v2"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    sector = Column(String(100), nullable=False)
    sources = Column(String(255), default="OpenStreetMap,DuckDuckGo")
    max_results = Column(Integer, default=30)
    last_run = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="saved_searches")
