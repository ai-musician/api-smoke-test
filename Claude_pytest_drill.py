"""
SDET pad drill: YOU write the tests.
Run:  pytest pytest_drill.py -v

Enumeration checklist to say OUT LOUD before typing:
  1. happy path        4. empty / missing        7. ordering
  2. boundary          5. invalid type           8. error-raising (message too!)
  3. duplicates        6. malformed value        9. float precision (approx)
"""
import pytest


# ---------------------------------------------------------------------------
# Target functions (in the interview, these are GIVEN — you only write tests)
# ---------------------------------------------------------------------------

def parse_version(s):
    """Parse 'X.Y.Z' into a tuple (major, minor, patch) of ints.

    Raises TypeError for non-str input, ValueError for malformed strings.
    """
    if not isinstance(s, str):
        raise TypeError(f"expected str, got {type(s).__name__}")
    parts = s.split(".")
    if len(parts) != 3:
        raise ValueError(f"expected X.Y.Z, got {s!r}")
    if not all(p.isdigit() for p in parts):        # rejects '', '-1', ' 1'
        raise ValueError(f"non-numeric component in {s!r}")
    return tuple(int(p) for p in parts)


def apply_discount(price, percent):
    """Return price after a percent discount. 0 <= percent <= 100, price >= 0."""
    if not isinstance(price, (int, float)) or isinstance(price, bool):
        raise TypeError("price must be a number")
    if price < 0:
        raise ValueError("price must be non-negative")
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return price * (1 - percent / 100)


# ---------------------------------------------------------------------------
# Tests for parse_version
# ---------------------------------------------------------------------------

class TestParseVersion:

    # 1. happy path — parametrize with ids so failures read well
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("1.2.3", (1, 2, 3)),
            ("0.0.0", (0, 0, 0)),          # boundary: all zeros
            ("10.20.30", (10, 20, 30)),    # multi-digit
            ("999.0.1", (999, 0, 1)),      # boundary: large major
        ],
        ids=["simple", "zeros", "multi-digit", "large-major"],
    )
    def test_happy_path(self, text, expected):
        assert parse_version(text) == expected

    # 6. malformed values — one raises-check per shape of badness
    @pytest.mark.parametrize(
        "bad",
        ["", "1.2", "1.2.3.4", "a.b.c", "1..3", "1.2.x",
         "-1.2.3", " 1.2.3", "1.2.3 "],
        ids=["empty", "too-few", "too-many", "letters", "blank-part",
             "trailing-letter", "negative", "leading-space", "trailing-space"],
    )
    def test_malformed_raises_value_error(self, bad):
        with pytest.raises(ValueError):
            parse_version(bad)

    # 5. invalid type — TypeError, not ValueError (the distinction scores points)
    @pytest.mark.parametrize("bad", [None, 123, 1.23, ["1", "2", "3"], ("1.2.3",)],
                             ids=["none", "int", "float", "list", "tuple"])
    def test_non_string_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            parse_version(bad)

    # 8. error message content — match= is a regex
    def test_error_message_names_the_input(self):
        with pytest.raises(ValueError, match=r"1\.2"):
            parse_version("1.2")

    # 7. ordering — tuples give correct semantic comparison ("1.10.0" > "1.9.0",
    #    which naive string comparison gets wrong)
    def test_versions_sort_semantically(self):
        raw = ["1.10.0", "1.2.0", "1.9.0"]
        assert sorted(raw, key=parse_version) == ["1.2.0", "1.9.0", "1.10.0"]

    # 3. duplicates — equal inputs parse equal (safe as dict keys / set members)
    def test_duplicate_versions_are_equal(self):
        assert parse_version("1.2.3") == parse_version("1.2.3")
        assert len({parse_version("1.2.3"), parse_version("1.2.3")}) == 1


# ---------------------------------------------------------------------------
# Tests for apply_discount
# ---------------------------------------------------------------------------

class TestApplyDiscount:

    # 1 + 2. happy path AND boundaries in one table (0% and 100% are the edges)
    @pytest.mark.parametrize(
        "price, percent, expected",
        [
            (100, 25, 75.0),
            (100, 0, 100.0),     # boundary: no discount
            (100, 100, 0.0),     # boundary: full discount
            (0, 50, 0.0),        # boundary: free item
            (19.99, 10, 17.991), # float math -> use approx in the assert
        ],
        ids=["quarter-off", "zero-pct", "full-pct", "zero-price", "float-price"],
    )
    def test_discount_values(self, price, percent, expected):
        # 9. never == on floats: pytest.approx
        assert apply_discount(price, percent) == pytest.approx(expected)

    # 8. out-of-range inputs — check the message, not just the exception type
    @pytest.mark.parametrize("percent", [-1, 100.01, 500])
    def test_percent_out_of_range(self, percent):
        with pytest.raises(ValueError, match="between 0 and 100"):
            apply_discount(100, percent)

    def test_negative_price(self):
        with pytest.raises(ValueError, match="non-negative"):
            apply_discount(-5, 10)

    # 5. invalid type — including the bool trap (bool is a subclass of int!)
    @pytest.mark.parametrize("bad", ["100", None, [100], True],
                             ids=["str", "none", "list", "bool"])
    def test_price_wrong_type(self, bad):
        with pytest.raises(TypeError):
            apply_discount(bad, 10)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
