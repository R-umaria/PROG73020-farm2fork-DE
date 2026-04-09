from app.repositories.driver_repository import DriverRepository
from app.services.driver_assignment_policy import DriverAssignmentPolicy


def test_select_driver_prefers_lower_current_load():
    policy = DriverAssignmentPolicy(DriverRepository())

    selection = policy.select_driver({1: 2, 2: 0})

    assert selection is not None
    assert selection.driver.id == 2
    assert selection.current_load == 0


def test_select_driver_uses_stable_tie_breaking_by_driver_id():
    policy = DriverAssignmentPolicy(DriverRepository())

    selection = policy.select_driver({1: 1, 2: 1})

    assert selection is not None
    assert selection.driver.id == 1
    assert selection.current_load == 1
