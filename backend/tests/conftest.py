import pytest

SUPABASE_VARIABLES = ('SUPABASE_URL', 'SUPABASE_SECRET_KEY')


@pytest.fixture(autouse=True)
def no_live_database(request, monkeypatch):
    """No test may reach the real database by accident: Supabase settings are removed from the
    environment, except for tests marked `live` (tests/integration/, run on purpose)."""
    if request.node.get_closest_marker('live') is None:
        for name in SUPABASE_VARIABLES:
            monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def no_rate_limit_by_default(monkeypatch):
    """Most tests send many requests from one client; the rate-limit tests set their own limit."""
    monkeypatch.setenv('MORTGAGE_RATE_LIMIT', 'off')
