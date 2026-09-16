from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    verification_status = Column(String(30), nullable=False, default="pending", index=True)
    verification_updated_at = Column(DateTime, nullable=True)
    company_name = Column(String(200), nullable=True)
    company_domain = Column(String(253), nullable=True)
    intended_use = Column(String(500), nullable=True)
    company_profile_submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    scans = relationship("Scan", back_populates="user")
    targets = relationship("Target", back_populates="user")
    verification_reviews = relationship("VerificationReviewAudit", back_populates="user", cascade="all, delete-orphan")
    entitlement = relationship("Entitlement", back_populates="user", uselist=False, cascade="all, delete-orphan")
    entitlement_installations = relationship("EntitlementInstallation", back_populates="user", cascade="all, delete-orphan")
    entitlement_audits = relationship("EntitlementLifecycleAudit", back_populates="user", cascade="all, delete-orphan")
    engagements = relationship("Engagement", back_populates="user", cascade="all, delete-orphan")


class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True)
    domain = Column(String(253), nullable=False, unique=True, index=True)
    verification_token = Column(String(128), nullable=False)
    status = Column(String(30), nullable=False, default="pending", index=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="targets")
    scans = relationship("Scan", back_populates="verified_target")


class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True)
    target = Column(String(2048), nullable=False)
    scanner = Column(String(50), nullable=False, default="web-security")
    status = Column(String(30), nullable=False, default="running")
    error = Column(Text, nullable=True)
    scan_profile = Column(String(30), nullable=False, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=True)
    user = relationship("User", back_populates="scans")
    verified_target = relationship("Target", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)

    # Public engine identity. The concrete adapter/tool is intentionally kept
    # behind the backend boundary so the customer UI stays scanner-agnostic.
    scanner = Column(String(50), nullable=False, default="web-security")

    # Stable normalized finding metadata used by every future scanner adapter.
    rule_id = Column(String(120), nullable=True, index=True)
    category = Column(String(120), nullable=True)

    severity = Column(String(20), nullable=False, default="info")
    title = Column(String(500), nullable=False)
    url = Column(String(2048), nullable=True)
    description = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    reference = Column(Text, nullable=True)

    # Optional internal/raw source evidence. It is not exposed as a vendor name
    # in the customer-facing UI.
    raw_output = Column(Text, nullable=True)

    scan = relationship("Scan", back_populates="findings")


class VerificationReviewAudit(Base):
    __tablename__ = "verification_review_audit"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    actor_id = Column(String(120), nullable=False)
    actor_role = Column(String(30), nullable=False)
    source = Column(String(50), nullable=False, default="trusted-admin")
    from_status = Column(String(30), nullable=False)
    to_status = Column(String(30), nullable=False)
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="verification_reviews")


class Entitlement(Base):
    __tablename__ = "entitlements"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    product_key = Column(String(30), nullable=False)
    authority_status = Column(String(30), nullable=False, default="blocked", index=True)
    valid_until = Column(DateTime, nullable=True)
    license_id = Column(String(120), nullable=True, unique=True, index=True)
    seat_limit = Column(Integer, nullable=False, default=1)
    issued_at = Column(DateTime, nullable=True)
    source = Column(String(50), nullable=False, default="entitlement-authority")
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="entitlement")


class EntitlementInstallation(Base):
    __tablename__ = "entitlement_installations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    installation_id = Column(String(120), nullable=False, unique=True, index=True)
    status = Column(String(30), nullable=False, default="active", index=True)
    bound_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    released_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="entitlement_installations")


class EntitlementLifecycleAudit(Base):
    __tablename__ = "entitlement_lifecycle_audit"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    actor_id = Column(String(120), nullable=False)
    actor_role = Column(String(30), nullable=False)
    action = Column(String(30), nullable=False)
    license_id = Column(String(120), nullable=True)
    installation_id = Column(String(120), nullable=True)
    detail = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="entitlement_audits")


class Engagement(Base):
    __tablename__ = "engagements"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reference = Column(String(120), nullable=False, unique=True, index=True)
    customer_name = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False, default="approved", index=True)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    approved_by = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="engagements")
    scopes = relationship("EngagementScope", back_populates="engagement", cascade="all, delete-orphan")


class EngagementScope(Base):
    __tablename__ = "engagement_scopes"
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=False, index=True)
    hostname = Column(String(253), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    engagement = relationship("Engagement", back_populates="scopes")


class EngagementAudit(Base):
    __tablename__ = "engagement_audit"
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, nullable=True, index=True)
    actor_id = Column(String(120), nullable=False)
    actor_role = Column(String(30), nullable=False)
    action = Column(String(30), nullable=False)
    reference = Column(String(120), nullable=False)
    detail = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
