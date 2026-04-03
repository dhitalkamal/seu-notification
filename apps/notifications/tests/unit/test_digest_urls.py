"""Tests confirming digest URL patterns resolve correctly."""

from __future__ import annotations


def test_digest_schedule_urlpatterns_exist():
    """URL module exports a urlpatterns list."""
    from apps.notifications.presentation import digest_urls

    assert hasattr(digest_urls, "urlpatterns")
    assert len(digest_urls.urlpatterns) == 2


def test_digest_schedule_list_create_url_name():
    """List/create route has the correct name."""
    from apps.notifications.presentation import digest_urls

    names = [p.name for p in digest_urls.urlpatterns]
    assert "digest-schedule-list-create" in names


def test_digest_schedule_detail_url_name():
    """Detail route has the correct name."""
    from apps.notifications.presentation import digest_urls

    names = [p.name for p in digest_urls.urlpatterns]
    assert "digest-schedule-detail" in names
