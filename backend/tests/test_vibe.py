from app.services.vibe import genre_waypoints, pace_for_genres


def test_genre_walk_ramps_from_rap_toward_folk():
    start = ["rap", "r&b"]
    end = ["indie", "folk"]
    assert pace_for_genres(start) > pace_for_genres(end)
    points = genre_waypoints(start, end, 4)
    assert len(points) == 4
    assert points[0] in {"rap", "r&b", "hip hop", "pop rap", "soul", "pop"}
    assert points[-1] in {"folk", "indie", "indie folk", "indie pop", "singer-songwriter"}
