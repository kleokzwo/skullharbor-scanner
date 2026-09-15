from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    scans = relationship("Scan", back_populates="user")
    targets = relationship("Target", back_populates="user")


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
