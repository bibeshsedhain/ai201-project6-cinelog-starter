# PR Response Doc — CineLog Watchlist Feature

## AI Usage

Codex was used to inspect the collection service and existing tests, locate the watchlist function and its callers with a repository-wide search, apply the Comment 1 rename, and run the existing test suite. Codex also compared the collection deduplication pattern, implemented the Comment 2 duplicate check and HTTP conflict response, and verified duplicate and independent user/film cases in an isolated in-memory database. For Comment 3, Codex used the existing nonexistent-film collection test as a model, added the watchlist equivalent, and ran the targeted test and full suite. Comments 4–6 have not been addressed yet.

## Comment 1 — Rename

**What I did:** Renamed `save_to_watchlist()` to `add_to_watchlist()` in `services/watchlist_service.py`, following the `add_to_collection()` naming pattern. Updated both the import and the call inside `add_film()` in `routes/watchlist/watchlist.py`. This change preserves the existing endpoint and behavior.

**How I verified:** Before editing, a repository-wide `rg -n 'save_to_watchlist|add_to_watchlist' .` search identified the service definition, the route import, and the route call. After editing, `rg -n 'save_to_watchlist|add_to_watchlist' --glob '*.py' .` showed exactly those three references using the new name and no Python references using the old name. The old name appears here only to describe the rename. Ran `.venv/bin/python -m pytest tests/ -v`: all four existing tests passed. Those tests exercise collections, so I also checked the watchlist endpoint directly with Flask's test client to verify its updated import and call create a watchlist entry successfully.


## Comment 2 — Deduplication

**What I did:** Followed the existing `add_to_collection()` pattern in `services/collection_service.py`: after verifying the film exists, query for an entry matching both `user_id` and `film_id` with `.filter_by(...).first()`. The collection service raises `AlreadyInCollectionError` when it finds that pair. The watchlist service now performs the equivalent check on `WatchlistEntry` and raises `AlreadyInWatchlistError` before adding or committing a second entry. The watchlist route converts that exception into a JSON error with HTTP 409, matching the collection route's conflict response. Different users can still save the same film, and a user can still save different films.

**How I verified:** Ran `.venv/bin/python -m pytest tests/ -v`; all four existing tests passed. In a separate in-memory database smoke check, the first API add returned 201; a repeated service call raised `AlreadyInWatchlistError`; and a repeated API add returned 409 with an error message. Confirmed the original user/film pair still had exactly one row. Adding the same film for another user and a different film for the original user both returned 201, leaving three distinct entries total. These were direct verification checks; the requested nonexistent-film test remains a separate change for Comment 3.


## Comment 3 — Missing test

**What I did:** Added `test_add_to_watchlist_nonexistent_film_raises()` in `tests/test_watchlist.py`, modeled after `test_add_to_collection_nonexistent_film_raises()` in `tests/test_collection.py`. It follows the same in-memory app fixture, persisted sample user, application context, and `pytest.raises(FilmNotFoundError)` structure. The test uses a film ID that is absent from the catalog, explicitly confirms that absence, and checks that calling `add_to_watchlist()` raises the intended service error. It also verifies that no watchlist entry was saved. This targets a nonexistent `film_id`, rather than a duplicate, missing request field, or nonexistent user.

**How I verified:** Ran `.venv/bin/python -m pytest tests/test_watchlist.py -v`: the new test passed. Then ran `.venv/bin/python -m pytest tests/ -v`: all five tests passed.
