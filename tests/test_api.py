"""Regression coverage for the API.

Every test here pins a defect that was live in the pre-review code, so a
future change that reintroduces one fails loudly.
"""

from __future__ import annotations

import pytest


def test_seed_data_is_loaded(client):
    result = client.get("/api/figures").get_json()
    assert result["total"] == 20
    assert len(result["items"]) == 20


def test_figures_response_is_paginated(client):
    result = client.get("/api/figures?per_page=5&page=2").get_json()
    assert result["page"] == 2
    assert result["per_page"] == 5
    assert result["pages"] == 4
    assert len(result["items"]) == 5


def test_per_page_is_capped(client, app_module):
    result = client.get("/api/figures?per_page=100000").get_json()
    assert result["per_page"] == app_module.MAX_PER_PAGE


class TestInputValidation:
    """Junk query parameters used to raise ValueError and return a 500."""

    def test_non_numeric_min_price_is_a_client_error(self, client):
        response = client.get("/api/figures?min_price=abc")
        assert response.status_code == 400
        assert "min_price" in response.get_json()["error"]

    def test_non_numeric_figure_id_is_a_client_error(self, client):
        assert client.get("/api/prices?figure_id=oops").status_code == 400

    def test_page_below_one_is_rejected(self, client):
        assert client.get("/api/figures?page=0").status_code == 400

    def test_malformed_json_body_is_a_client_error(self, client):
        response = client.post("/api/prices", data="not json", content_type="application/json")
        assert response.status_code == 400

    def test_json_array_body_is_rejected(self, client):
        assert client.post("/api/figures", json=[1, 2, 3]).status_code == 400

    def test_api_errors_are_json_not_html(self, client):
        response = client.get("/api/figures?min_price=abc")
        assert response.mimetype == "application/json"

    @pytest.mark.parametrize("value", [1.5, True, [], {}, 2147483648, 1e100])
    def test_invalid_integer_values_are_rejected(self, client, value):
        response = client.post("/api/figures", json={"name": "Invalid", "official_price": value})
        assert response.status_code == 400

    @pytest.mark.parametrize("field", ["official_price", "height_mm"])
    def test_negative_figure_numbers_are_rejected(self, client, field):
        assert client.post("/api/figures", json={"name": "Invalid", field: -1}).status_code == 400

    def test_negative_purchase_price_is_rejected(self, client):
        assert client.post("/api/collection", json={"figure_id": 1, "purchase_price": -1}).status_code == 400

    @pytest.mark.parametrize("value", ["2026-02-30", "2026-13", "tomorrow"])
    def test_invalid_release_date_is_rejected(self, client, value):
        assert client.post("/api/figures", json={"name": "Invalid", "release_date": value}).status_code == 400

    @pytest.mark.parametrize("value", ["2026-02", "2026-02-30", "20260201", "2026-2-1"])
    def test_invalid_checked_date_is_rejected(self, client, value):
        response = client.post(
            "/api/prices", json={"figure_id": 1, "shop_name": "x", "price": 10, "checked_date": value}
        )
        assert response.status_code == 400

    def test_invalid_purchase_date_and_status_are_rejected(self, client):
        for fields in ({"purchase_date": "2026-02-30"}, {"ownership_status": "unknown"}):
            assert client.post("/api/collection", json={"figure_id": 1, **fields}).status_code == 400

    @pytest.mark.parametrize("value", ["2026-02", "2028-02-29"])
    def test_month_and_day_release_dates_are_supported(self, client, value):
        assert client.post("/api/figures", json={"name": "Valid", "release_date": value}).status_code == 201

    def test_invalid_boolean_and_text_values_are_rejected(self, client):
        for fields in ({"is_limited": "maybe"}, {"name": {"bad": "name"}}):
            assert client.post("/api/figures", json={"name": "Invalid", **fields}).status_code == 400

    def test_zero_prices_are_valid(self, client):
        assert client.post("/api/figures", json={"name": "Free", "official_price": 0}).status_code == 201

    def test_out_of_range_page_returns_the_last_page(self, client):
        result = client.get("/api/figures?per_page=5&page=999999999999999999999").get_json()
        assert result["page"] == result["pages"] == 4
        assert len(result["items"]) == 5


class TestKeywordSearch:
    def test_percent_is_treated_as_a_literal_not_a_wildcard(self, client):
        result = client.get("/api/figures?keyword=%25").get_json()
        assert result["total"] == 0

    def test_underscore_is_treated_as_a_literal(self, client):
        result = client.get("/api/figures?keyword=_").get_json()
        assert result["total"] == 0

    def test_keyword_still_matches_real_text(self, client):
        result = client.get("/api/figures?keyword=Figuarts").get_json()
        assert result["total"] > 0

    def test_keyword_is_case_insensitive(self, client):
        lower = client.get("/api/figures?keyword=figuarts").get_json()["total"]
        upper = client.get("/api/figures?keyword=FIGUARTS").get_json()["total"]
        assert lower == upper > 0


class TestMissingRecords:
    """Deleting a non-existent row used to report success."""

    def test_delete_missing_price_is_404(self, client):
        assert client.delete("/api/prices/99999").status_code == 404

    def test_delete_missing_collection_is_404(self, client):
        assert client.delete("/api/collection/99999").status_code == 404

    def test_delete_missing_figure_is_404(self, client):
        assert client.delete("/api/figures/99999").status_code == 404

    def test_get_missing_figure_is_404(self, client):
        assert client.get("/api/figures/99999").status_code == 404

    def test_price_for_unknown_figure_is_404(self, client):
        response = client.post(
            "/api/prices",
            json={"figure_id": 99999, "shop_name": "x", "price": 100, "checked_date": "2026-01-01"},
        )
        assert response.status_code == 404


class TestPartialUpdate:
    """A PUT with a subset of fields must not reset the omitted ones."""

    def test_omitted_fields_are_preserved(self, client):
        created = client.post(
            "/api/collection",
            json={
                "figure_id": 1,
                "ownership_status": "所持",
                "purchase_price": 9999,
                "purchase_shop": "あみあみ",
                "memo": "keep me",
            },
        ).get_json()

        client.put(f"/api/collection/{created['id']}", json={"purchase_price": 8888})

        row = client.get("/api/collection?figure_id=1").get_json()["items"][0]
        assert row["purchase_price"] == 8888
        assert row["ownership_status"] == "所持"
        assert row["purchase_shop"] == "あみあみ"
        assert row["memo"] == "keep me"

    def test_update_with_no_known_fields_is_rejected(self, client):
        created = client.post("/api/collection", json={"figure_id": 2}).get_json()
        assert client.put(f"/api/collection/{created['id']}", json={"nope": 1}).status_code == 400

    def test_update_missing_record_is_404(self, client):
        assert client.put("/api/collection/99999", json={"purchase_price": 1}).status_code == 404

    def test_readding_a_collection_preserves_omitted_fields(self, client):
        created = client.post(
            "/api/collection",
            json={"figure_id": 1, "ownership_status": "所持", "is_opened": True, "memo": "keep"},
        ).get_json()
        response = client.post("/api/collection", json={"figure_id": 1, "purchase_price": 1234})
        assert response.get_json()["id"] == created["id"]
        row = client.get("/api/collection?figure_id=1").get_json()["items"][0]
        assert row["ownership_status"] == "所持"
        assert row["is_opened"] == 1
        assert row["memo"] == "keep"
        assert row["purchase_price"] == 1234

    def test_readding_with_only_figure_id_preserves_existing_record(self, client):
        before = client.get("/api/collection?figure_id=1").get_json()["items"][0]
        assert client.post("/api/collection", json={"figure_id": 1}).status_code == 201
        after = client.get("/api/collection?figure_id=1").get_json()["items"][0]
        for key in ("id", "ownership_status", "is_opened", "purchase_price", "memo"):
            assert before[key] == after[key]


class TestFigureCrud:
    def test_create_update_delete_round_trip(self, client):
        created = client.post("/api/figures", json={"name": "Test Figure", "official_price": 5000})
        assert created.status_code == 201
        figure_id = created.get_json()["id"]

        assert client.put(f"/api/figures/{figure_id}", json={"official_price": 6000}).status_code == 200
        figure = client.get(f"/api/figures/{figure_id}").get_json()
        assert figure["official_price"] == 6000
        assert figure["name"] == "Test Figure"

        assert client.delete(f"/api/figures/{figure_id}").status_code == 200
        assert client.get(f"/api/figures/{figure_id}").status_code == 404

    def test_name_is_required(self, client):
        assert client.post("/api/figures", json={"brand": "x"}).status_code == 400
        assert client.post("/api/figures", json={"name": "   "}).status_code == 400

    def test_deleting_a_figure_cascades_to_its_records(self, client):
        client.post("/api/collection", json={"figure_id": 1, "ownership_status": "所持"})
        assert client.get("/api/prices?figure_id=1").get_json()["total"] > 0

        client.delete("/api/figures/1")

        assert client.get("/api/prices?figure_id=1").get_json()["total"] == 0
        assert client.get("/api/collection?figure_id=1").get_json()["total"] == 0


class TestPriceMovement:
    """`prev_price` is resolved in SQL so it survives filtering and paging."""

    def test_first_record_for_a_shop_has_no_previous_price(self, client):
        rows = client.get("/api/prices/1").get_json()
        first = min(rows, key=lambda row: (row["checked_date"], row["id"]))
        assert first["prev_price"] is None

    def test_previous_price_is_scoped_per_shop(self, client):
        figure_id = client.post("/api/figures", json={"name": "Trend Target"}).get_json()["id"]
        for shop, price, date in [
            ("shop-a", 1000, "2026-01-01"),
            ("shop-b", 5000, "2026-01-02"),
            ("shop-a", 1200, "2026-01-03"),
        ]:
            client.post(
                "/api/prices",
                json={"figure_id": figure_id, "shop_name": shop, "price": price, "checked_date": date},
            )

        rows = {(r["shop_name"], r["checked_date"]): r for r in client.get(f"/api/prices/{figure_id}").get_json()}
        assert rows[("shop-a", "2026-01-01")]["prev_price"] is None
        assert rows[("shop-b", "2026-01-02")]["prev_price"] is None
        # shop-b's row sits between the two shop-a rows but must not leak in.
        assert rows[("shop-a", "2026-01-03")]["prev_price"] == 1000

    def test_previous_price_survives_pagination(self, client):
        figure_id = client.post("/api/figures", json={"name": "Paged Trend"}).get_json()["id"]
        for index in range(4):
            client.post(
                "/api/prices",
                json={
                    "figure_id": figure_id,
                    "shop_name": "solo",
                    "price": 1000 + index * 100,
                    "checked_date": f"2026-02-0{index + 1}",
                },
            )
        # Newest first, one row per page: page 2 holds the 1200 row while its
        # predecessor (1100) sits on page 3, outside the returned window.
        page = client.get(f"/api/prices?figure_id={figure_id}&per_page=1&page=2").get_json()
        assert page["items"][0]["price"] == 1200
        assert page["items"][0]["prev_price"] == 1100

    def test_negative_price_is_rejected(self, client):
        response = client.post(
            "/api/prices",
            json={"figure_id": 1, "shop_name": "x", "price": -5, "checked_date": "2026-01-01"},
        )
        assert response.status_code == 400


class TestDashboard:
    def test_dashboard_payload_is_complete(self, client):
        data = client.get("/api/dashboard").get_json()
        for key in (
            "total_figures",
            "owned_count",
            "wishlist_budget",
            "reserved_budget",
            "brand_distribution",
            "price_buckets",
            "monthly_releases",
            "purchase_by_brand",
        ):
            assert key in data

    def test_figures_without_a_price_are_excluded_from_price_bands(self, client):
        before = sum(bucket["count"] for bucket in client.get("/api/dashboard").get_json()["price_buckets"])
        client.post("/api/figures", json={"name": "No Price Figure"})
        after = sum(bucket["count"] for bucket in client.get("/api/dashboard").get_json()["price_buckets"])
        assert after == before

    def test_options_carry_figure_id_name_pairs(self, client):
        options = client.get("/api/options").get_json()
        assert len(options["figures"]) == 20
        assert set(options["figures"][0]) == {"id", "name"}


class TestWriteGuard:
    def test_local_development_allows_writes_without_a_token(self, client):
        assert client.get("/api/config").get_json() == {"writes_open": True, "auth_required": False}
        assert client.post("/api/figures", json={"name": "Local"}).status_code == 201

    def test_deployment_without_a_token_is_read_only(self, tmp_path, monkeypatch):
        from conftest import load_app

        module = load_app(tmp_path, monkeypatch, VERCEL="1")
        client = module.app.test_client()
        assert client.get("/api/figures").status_code == 200
        assert client.post("/api/figures", json={"name": "Nope"}).status_code == 403
        assert client.delete("/api/collection/1").status_code == 403

    def test_deployment_with_a_token_requires_the_header(self, tmp_path, monkeypatch):
        from conftest import load_app

        module = load_app(tmp_path, monkeypatch, VERCEL="1", FIGURE_DASHBOARD_TOKEN="s3cret")
        client = module.app.test_client()

        assert client.get("/api/figures").status_code == 200
        assert client.post("/api/figures", json={"name": "Nope"}).status_code == 401
        assert client.post(
            "/api/figures", json={"name": "Nope"}, headers={"X-Auth-Token": "wrong"}
        ).status_code == 401
        assert client.post(
            "/api/figures", json={"name": "Yes"}, headers={"X-Auth-Token": "s3cret"}
        ).status_code == 201


class TestSchemaLifecycle:
    def test_init_db_is_not_destructive(self, app_module, client):
        client.post("/api/figures", json={"name": "Survivor"})
        before = client.get("/api/figures").get_json()["total"]

        app_module.init_database(seed=True, reset=False)

        assert client.get("/api/figures").get_json()["total"] == before
        assert client.get("/api/figures?keyword=Survivor").get_json()["total"] == 1

    def test_reset_db_rebuilds_from_seed(self, app_module, client):
        client.post("/api/figures", json={"name": "Survivor"})

        app_module.init_database(seed=True, reset=True)

        result = client.get("/api/figures").get_json()
        assert result["total"] == 20
        assert client.get("/api/figures?keyword=Survivor").get_json()["total"] == 0


class TestPages:
    def test_every_page_renders(self, client):
        for path in ("/", "/figures", "/figures/1", "/collection", "/prices"):
            assert client.get(path).status_code == 200

    def test_pages_carry_a_cache_busting_asset_version(self, client, app_module):
        body = client.get("/").get_data(as_text=True)
        assert f"?v={app_module.ASSET_VERSION}" in body

    def test_unknown_page_is_a_normal_404(self, client):
        assert client.get("/no-such-page").status_code == 404

    def test_missing_figure_detail_page_is_404(self, client):
        assert client.get("/figures/99999").status_code == 404
