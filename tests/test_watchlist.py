"""Tests for the watchlist service."""

import pytest
from app import create_app, db
from models import User, Film, WatchlistEntry
from services.collection_service import FilmNotFoundError
from services.watchlist_service import (
    NotInWatchlistError,
    add_to_watchlist,
    remove_from_watchlist,
)


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


def test_remove_from_watchlist_preserves_other_users_entries(app, sample_user):
    with app.app_context():
        film = Film(title="Alien")
        other_user = User(username="anotheruser", email="another@example.com")
        db.session.add_all([film, other_user])
        db.session.commit()
        film_id, other_user_id = film.id, other_user.id

        add_to_watchlist(sample_user, film_id)
        add_to_watchlist(other_user_id, film_id)

        assert remove_from_watchlist(sample_user, film_id) is True
        remaining = WatchlistEntry.query.filter_by(film_id=film_id).one()
        assert remaining.user_id == other_user_id

        with pytest.raises(NotInWatchlistError):
            remove_from_watchlist(sample_user, film_id)


def test_duplicate_add_cannot_change_visibility(app, sample_user):
    with app.app_context():
        film = Film(title="Alien")
        db.session.add(film)
        db.session.commit()
        film_id = film.id

    client = app.test_client()
    watchlist_url = f"/watchlist/{sample_user}"
    created = client.post(f"{watchlist_url}/add", json={
        "film_id": film_id,
        "public": False,
    })
    duplicate = client.post(f"{watchlist_url}/add", json={
        "film_id": film_id,
        "public": True,
    })

    assert created.status_code == 201
    assert created.get_json()["public"] is False
    assert duplicate.status_code == 409
    entries = client.get(watchlist_url).get_json()
    assert [(entry["id"], entry["public"]) for entry in entries] == [(film_id, False)]
