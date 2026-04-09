from app.services.planning_service import PlanningService


def test_derive_region_key_uses_postal_prefix_first():
    region_key, source, postal_prefix = PlanningService.derive_region_key(
        postal_code="m5v 1a1",
        city="Toronto",
        province="ON",
    )

    assert region_key == "postal_prefix:M5V"
    assert source == "postal_prefix"
    assert postal_prefix == "M5V"


def test_derive_region_key_falls_back_to_city_and_province_when_postal_missing():
    region_key, source, postal_prefix = PlanningService.derive_region_key(
        postal_code="  ",
        city="St. Catharines",
        province="ON",
    )

    assert region_key == "city_province:ST_CATHARINES:ON"
    assert source == "city_province"
    assert postal_prefix is None
