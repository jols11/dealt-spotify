from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from app.analytics.sessions import PlayRecord

HOUR_BUCKETS = (
    ("Late night", (0, 5)),
    ("Morning", (5, 12)),
    ("Afternoon", (12, 17)),
    ("Evening", (17, 21)),
    ("Night", (21, 24)),
)

SEASONS = {
    12: "Winter",
    1: "Winter",
    2: "Winter",
    3: "Spring",
    4: "Spring",
    5: "Spring",
    6: "Summer",
    7: "Summer",
    8: "Summer",
    9: "Fall",
    10: "Fall",
    11: "Fall",
}

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


@dataclass
class BucketStats:
    label: str
    event_count: int
    unique_artists: int
    top_artist: str | None
    top_artist_share: float
    repeat_rate: float


@dataclass
class TemporalProfile:
    hours: list[dict]
    hour_buckets: list[BucketStats]
    weekdays: list[BucketStats]
    months: list[BucketStats]
    seasons: list[BucketStats]
    peak_hour: int | None
    peak_hour_insight: str
    peak_weekday: str | None
    peak_weekday_insight: str


def _bucket_stats(label: str, events: list[PlayRecord]) -> BucketStats:
    if not events:
        return BucketStats(label, 0, 0, None, 0.0, 0.0)
    artist_counts = Counter(event.artist_id for event in events)
    names = {event.artist_id: event.artist_name for event in events}
    top_id, top_count = artist_counts.most_common(1)[0]
    unique_tracks = len({event.track_id for event in events})
    return BucketStats(
        label=label,
        event_count=len(events),
        unique_artists=len(artist_counts),
        top_artist=names[top_id],
        top_artist_share=round(top_count / len(events), 4),
        repeat_rate=round(1.0 - unique_tracks / len(events), 4),
    )


def hour_bucket(hour: int) -> str:
    for label, (start, end) in HOUR_BUCKETS:
        if start <= hour < end:
            return label
    return "Night"


def compute_temporal(events: list[PlayRecord]) -> TemporalProfile:
    if not events:
        return TemporalProfile(
            hours=[],
            hour_buckets=[],
            weekdays=[],
            months=[],
            seasons=[],
            peak_hour=None,
            peak_hour_insight="Not enough plays to describe when you listen.",
            peak_weekday=None,
            peak_weekday_insight="Not enough plays to describe weekly rhythm.",
        )

    by_hour: dict[int, list[PlayRecord]] = defaultdict(list)
    by_bucket: dict[str, list[PlayRecord]] = defaultdict(list)
    by_weekday: dict[str, list[PlayRecord]] = defaultdict(list)
    by_month: dict[str, list[PlayRecord]] = defaultdict(list)
    by_season: dict[str, list[PlayRecord]] = defaultdict(list)

    for event in events:
        local = event.played_at
        hour = local.hour
        by_hour[hour].append(event)
        by_bucket[hour_bucket(hour)].append(event)
        by_weekday[WEEKDAYS[local.weekday()]].append(event)
        by_month[MONTHS[local.month - 1]].append(event)
        by_season[SEASONS[local.month]].append(event)

    hours = [
        {
            "hour": hour,
            "label": f"{hour:02d}:00",
            "event_count": len(by_hour.get(hour, [])),
            "bucket": hour_bucket(hour),
        }
        for hour in range(24)
    ]
    peak_hour = max(range(24), key=lambda hour: len(by_hour.get(hour, [])))
    peak_bucket = hour_bucket(peak_hour)
    if peak_bucket in {"Night", "Late night"}:
        peak_hour_insight = f"Your listening peaks late at night, around {peak_hour:02d}:00."
    elif peak_bucket == "Morning":
        peak_hour_insight = f"Your listening peaks in the morning, around {peak_hour:02d}:00."
    elif peak_bucket == "Afternoon":
        peak_hour_insight = f"Afternoons are your busiest listening window, around {peak_hour:02d}:00."
    else:
        peak_hour_insight = f"Evenings are when you listen most, around {peak_hour:02d}:00."

    weekday_stats = [_bucket_stats(day, by_weekday.get(day, [])) for day in WEEKDAYS]
    peak_weekday = max(weekday_stats, key=lambda item: item.event_count).label
    if peak_weekday in {"Saturday", "Sunday"}:
        peak_weekday_insight = f"{peak_weekday} is your heaviest listening day — weekends pull ahead."
    else:
        peak_weekday_insight = f"{peak_weekday} is your heaviest listening day during the week."

    return TemporalProfile(
        hours=hours,
        hour_buckets=[_bucket_stats(label, by_bucket.get(label, [])) for label, _ in HOUR_BUCKETS],
        weekdays=weekday_stats,
        months=[_bucket_stats(month, by_month.get(month, [])) for month in MONTHS],
        seasons=[
            _bucket_stats(season, by_season.get(season, []))
            for season in ("Winter", "Spring", "Summer", "Fall")
        ],
        peak_hour=peak_hour,
        peak_hour_insight=peak_hour_insight,
        peak_weekday=peak_weekday,
        peak_weekday_insight=peak_weekday_insight,
    )


def weekly_evolution(events: list[PlayRecord]) -> list[dict]:
    grouped: dict[str, list[PlayRecord]] = defaultdict(list)
    for event in events:
        iso = event.played_at.isocalendar()
        key = f"{iso.year}-W{iso.week:02d}"
        grouped[key].append(event)
    series = []
    for key in sorted(grouped):
        bucket = grouped[key]
        artists = {event.artist_id for event in bucket}
        series.append(
            {
                "period": key,
                "plays": len(bucket),
                "unique_artists": len(artists),
            }
        )
    return series
