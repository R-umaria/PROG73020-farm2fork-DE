from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.db_models import CustomerDetails, DeliveryExecution, DeliveryItem, DeliveryRequest, RouteGroup, RouteStop, StatusHistory
from app.repositories.driver_portal_repository import DriverPortalRepository


class DemoSeedService:
    def __init__(self, db: Session | None = None):
        self.db: Session = db or SessionLocal()
        self.portal_repo = DriverPortalRepository(self.db)

    def seed(self) -> dict[str, int | str]:
        return {'driver_accounts': self._seed_driver_accounts(), 'available_shifts': self._seed_demo_shifts(), 'demo_driver_email': 'driver.demo@farm2fork.local'}

    def close(self) -> None:
        self.db.close()

    def _seed_driver_accounts(self) -> int:
        for driver_id, email, name, vehicle in [
            (1, 'driver.demo@farm2fork.local', 'Jordan Lee', 'Cargo Van'),
            (2, 'driver.sam@farm2fork.local', 'Sam Patel', 'Refrigerated Van'),
            (3, 'driver.avery@farm2fork.local', 'Avery Chen', 'Box Truck'),
        ]:
            self.portal_repo.create_or_update_driver_account(driver_id=driver_id, email=email, driver_name=name, vehicle_type=vehicle, driver_status='available', password_hash=hashlib.sha256(f'{email}:demo'.encode()).hexdigest())
        return 3

    def _seed_demo_shifts(self) -> int:
        existing = self.db.query(RouteGroup).filter(RouteGroup.name.in_(['Waterloo AM Shift', 'Kitchener Midday Shift'])).count()
        if existing >= 2:
            return existing
        now = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
        base_order_id = 700100
        shift_specs = [
            {'name': 'Waterloo AM Shift', 'zone_code': 'N2J', 'scheduled_date': now + timedelta(hours=1), 'distance': 18.6, 'duration_min': 56, 'customers': [('Alex Morgan', '519-555-0101', '200 University Ave W', 'Waterloo', 'ON', 'N2L 3G1', 43.4720, -80.5449), ('Taylor Brooks', '519-555-0102', '151 King St N', 'Waterloo', 'ON', 'N2J 2Y5', 43.4672, -80.5225), ('Casey Nguyen', '519-555-0103', '65 William St E', 'Waterloo', 'ON', 'N2J 1K8', 43.4648, -80.5180)]},
            {'name': 'Kitchener Midday Shift', 'zone_code': 'N2G', 'scheduled_date': now + timedelta(hours=3), 'distance': 22.1, 'duration_min': 68, 'customers': [('Riley Santos', '519-555-0104', '425 King St W', 'Kitchener', 'ON', 'N2G 1C1', 43.4512, -80.4924), ('Jamie Carter', '519-555-0105', '10 Duke St W', 'Kitchener', 'ON', 'N2H 3W5', 43.4519, -80.4891), ('Morgan Bell', '519-555-0106', '101 Frederick St', 'Kitchener', 'ON', 'N2H 2L2', 43.4538, -80.4857)]},
        ]
        for idx, spec in enumerate(shift_specs):
            if self.db.query(RouteGroup).filter(RouteGroup.name == spec['name']).first() is not None:
                continue
            group = RouteGroup(name=spec['name'], scheduled_date=spec['scheduled_date'], status='scheduled', zone_code=spec['zone_code'], total_stops=len(spec['customers']), estimated_distance_km=spec['distance'], estimated_duration_min=spec['duration_min'])
            self.db.add(group); self.db.flush()
            for seq, customer in enumerate(spec['customers'], start=1):
                cname, phone, street, city, province, postal, lat, lng = customer
                order_id = base_order_id + idx * 100 + seq
                request = DeliveryRequest(order_id=order_id, customer_id=9000 + order_id, request_timestamp=spec['scheduled_date'] - timedelta(minutes=45 - seq * 5), request_status='scheduled')
                self.db.add(request); self.db.flush()
                self.db.add(DeliveryItem(delivery_request_id=request.id, external_item_id=1000 + seq, item_name='Farm Box', quantity=1))
                self.db.add(CustomerDetails(delivery_request_id=request.id, customer_name=cname, phone_number=phone, street=street, city=city, province=province, postal_code=postal, country='Canada', latitude=lat, longitude=lng, geocode_status='seeded'))
                execution = DeliveryExecution(delivery_request_id=request.id, current_status='scheduled', retry_count=0)
                self.db.add(execution); self.db.flush()
                self.db.add(StatusHistory(delivery_execution_id=execution.id, old_status=None, new_status='scheduled', changed_by='system', reason='Demo seed created scheduled execution'))
                self.db.add(RouteStop(route_group_id=group.id, delivery_request_id=request.id, sequence=seq, estimated_arrival=spec['scheduled_date'] + timedelta(minutes=seq * 15), stop_status='scheduled'))
        self.db.commit(); return 2


def seed_demo_data_if_enabled() -> None:
    if not settings.demo_data_auto_seed:
        return
    service = DemoSeedService(SessionLocal())
    try:
        service.seed()
    finally:
        service.close()
