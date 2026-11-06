"""Tests for the watchlist service."""

import pytest
from app import create_app, db
from models import User, Film, WatchlistEntry
from services.collection_service import FilmNotFoundError
from services.watchlist_service import add_to_watchlist


@pytest.fixture
def app():
    """Create an isolated test app with an in-memory database."""
    app = create_app(config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_user(app):
    """A user to use in tests."""
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()
        return user.id


def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """A nonexistent film should raise FilmNotFoundError without saving an entry."""
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"
        assert db.session.get(Film, fake_film_id) is None

        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)

        assert WatchlistEntry.query.filter_by(user_id=sample_user).count() == 0
