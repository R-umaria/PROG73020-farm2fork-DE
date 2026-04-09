import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    DECIMAL,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DeliveryRequest(Base):
    __tablename__ = "delivery_request"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(BigInteger, nullable=False, index=True)
    customer_id = Column(BigInteger, nullable=False, index=True)
    request_timestamp = Column(DateTime(timezone=True), nullable=False)
    request_status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    items = relationship("DeliveryItem", back_populates="delivery_request", cascade="all, delete-orphan")
    request_snapshot = relationship("DeliveryRequestSnapshot", back_populates="delivery_request", uselist=False, cascade="all, delete-orphan")
    customer_details = relationship("CustomerDetails", back_populates="delivery_request", uselist=False, cascade="all, delete-orphan")
    customer_snapshot = relationship("CustomerDetailsSnapshot", back_populates="delivery_request", uselist=False, cascade="all, delete-orphan")
    execution = relationship("DeliveryExecution", back_populates="delivery_request", uselist=False, cascade="all, delete-orphan")
    route_stops = relationship("RouteStop", back_populates="delivery_request")


class DeliveryItem(Base):
    __tablename__ = "delivery_item"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_request_id = Column(UUID(as_uuid=True), ForeignKey("delivery_request.id"), nullable=False)
    external_item_id = Column(BigInteger, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

    delivery_request = relationship("DeliveryRequest", back_populates="items")


class DeliveryRequestSnapshot(Base):
    __tablename__ = "delivery_request_snapshot"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_request_id = Column(UUID(as_uuid=True), ForeignKey("delivery_request.id"), nullable=False, unique=True)
    request_payload = Column(JSON, nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    delivery_request = relationship("DeliveryRequest", back_populates="request_snapshot")


class CustomerDetails(Base):
    __tablename__ = "customer_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_request_id = Column(UUID(as_uuid=True), ForeignKey("delivery_request.id"), nullable=False, unique=True)
    customer_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    province = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    latitude = Column(DECIMAL(10, 7), nullable=True)
    longitude = Column(DECIMAL(10, 7), nullable=True)
    geocode_status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    delivery_request = relationship("DeliveryRequest", back_populates="customer_details")


class CustomerDetailsSnapshot(Base):
    __tablename__ = "customer_details_snapshot"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_request_id = Column(UUID(as_uuid=True), ForeignKey("delivery_request.id"), nullable=False, unique=True)
    customer_payload = Column(JSON, nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    delivery_request = relationship("DeliveryRequest", back_populates="customer_snapshot")


class RouteGroup(Base):
    __tablename__ = "route_group"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    zone_code = Column(String, nullable=False)
    total_stops = Column(Integer, nullable=False, default=0)
    estimated_distance_km = Column(DECIMAL(10, 2), nullable=True)
    estimated_duration_min = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    stops = relationship("RouteStop", back_populates="route_group", cascade="all, delete-orphan")
    driver_assignments = relationship("DriverAssignment", back_populates="route_group", cascade="all, delete-orphan")


class RouteStop(Base):
    __tablename__ = "route_stop"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_group_id = Column(UUID(as_uuid=True), ForeignKey("route_group.id"), nullable=False)
    delivery_request_id = Column(UUID(as_uuid=True), ForeignKey("delivery_request.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    estimated_arrival = Column(DateTime(timezone=True), nullable=True)
    stop_status = Column(String, nullable=False)

    route_group = relationship("RouteGroup", back_populates="stops")
    delivery_request = relationship("DeliveryRequest", back_populates="route_stops")


class DriverAssignment(Base):
    __tablename__ = "driver_assignment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_group_id = Column(UUID(as_uuid=True), ForeignKey("route_group.id"), nullable=False)
    driver_id = Column(BigInteger, nullable=False)
    assignment_status = Column(String, nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    unassigned_at = Column(DateTime(timezone=True), nullable=True)
    reassignment_reason = Column(String, nullable=True)

    route_group = relationship("RouteGroup", back_populates="driver_assignments")


class DeliveryExecution(Base):
    __tablename__ = "delivery_execution"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_request_id = Column(UUID(as_uuid=True), ForeignKey("delivery_request.id"), nullable=False, unique=True)
    current_status = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    out_for_delivery_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    delivery_request = relationship("DeliveryRequest", back_populates="execution")
    attempts = relationship("DeliveryAttempt", back_populates="delivery_execution", cascade="all, delete-orphan")
    confirmations = relationship("DeliveryConfirmation", back_populates="delivery_execution", cascade="all, delete-orphan")
    exceptions = relationship("DeliveryException", back_populates="delivery_execution", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="delivery_execution", cascade="all, delete-orphan")
    pickup_records = relationship("PickupRecord", back_populates="delivery_execution", cascade="all, delete-orphan")


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempt"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_execution_id = Column(UUID(as_uuid=True), ForeignKey("delivery_execution.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    attempted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    outcome = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    delivery_execution = relationship("DeliveryExecution", back_populates="attempts")


class DeliveryConfirmation(Base):
    __tablename__ = "delivery_confirmation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_execution_id = Column(UUID(as_uuid=True), ForeignKey("delivery_execution.id"), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    received_by = Column(String, nullable=False)
    proof_of_delivery_url = Column(Text, nullable=True)
    signature_data = Column(Text, nullable=True)

    delivery_execution = relationship("DeliveryExecution", back_populates="confirmations")


class DeliveryException(Base):
    __tablename__ = "delivery_exception"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_execution_id = Column(UUID(as_uuid=True), ForeignKey("delivery_execution.id"), nullable=False)
    exception_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    retry_allowed = Column(Boolean, nullable=False, default=False)

    delivery_execution = relationship("DeliveryExecution", back_populates="exceptions")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_execution_id = Column(UUID(as_uuid=True), ForeignKey("delivery_execution.id"), nullable=False)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    changed_by = Column(String, nullable=True)
    reason = Column(Text, nullable=True)

    delivery_execution = relationship("DeliveryExecution", back_populates="status_history")


class PickupRecord(Base):
    __tablename__ = "pickup_record"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_execution_id = Column(UUID(as_uuid=True), ForeignKey("delivery_execution.id"), nullable=False)
    picked_up_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    location = Column(String, nullable=True)
    collected_by = Column(String, nullable=True)

    delivery_execution = relationship("DeliveryExecution", back_populates="pickup_records")


class InternalEventRecord(Base):
    """Lightweight internal outbox-style record for future event publishing."""

    __tablename__ = "internal_event_record"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String, nullable=False)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(BigInteger, nullable=True, index=True)
    event_type = Column(String, nullable=False)
    event_payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
