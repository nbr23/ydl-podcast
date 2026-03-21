from ydl_podcast import flatten_entries


def test_flat_list():
    metadata = {"entries": [{"url": "a"}, {"url": "b"}, {"url": "c"}]}
    entries = []
    flatten_entries(metadata, entries)
    assert len(entries) == 3


def test_nested_playlist():
    metadata = {
        "entries": [
            {
                "_type": "playlist",
                "entries": [{"url": "a"}, {"url": "b"}],
            }
        ]
    }
    entries = []
    flatten_entries(metadata, entries)
    assert len(entries) == 2
    assert entries[0]["url"] == "a"


def test_empty():
    entries = []
    flatten_entries({}, entries)
    assert entries == []


def test_mixed():
    metadata = {
        "entries": [
            {"url": "a"},
            {
                "_type": "playlist",
                "entries": [{"url": "b"}, {"url": "c"}],
            },
            {"url": "d"},
        ]
    }
    entries = []
    flatten_entries(metadata, entries)
    assert len(entries) == 4
    assert [e["url"] for e in entries] == ["a", "b", "c", "d"]
