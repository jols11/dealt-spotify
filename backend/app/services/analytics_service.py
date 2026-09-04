from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from app.analytics.clusters import cluster_artists
from app.analytics.diversity import compute_diversity
from app.analytics.graph import build_transition_graph
from app.analytics.insights import overview_insights
from app.analytics.recommendations import recommend_revisits
from app.analytics.sessions import sessionize
from app.analytics.similarity import compare_users
from app.analytics.temporal import compute_temporal, weekly_evolution
from app.analytics.transitions import transitions_from_sessions
from app.core.config import get_settings
from app.models.entities import User
from app.services.demo_seed import synthetic_personas
from app.services.pipeline import load_play_records


def _asdict_bucket(item) -> dict:
    return {
        "label": item.label,
        "event_count": item.event_count,
        "unique_artists": item.unique_artists,
        "top_artist": item.top_artist,
        "top_artist_share": item.top_artist_share,
        "repeat_rate": item.repeat_rate,
    }


def assemble_analytics(db: Session, user: User) -> dict:
    settings = get_settings()
    events = load_play_records(db, user.id)
    sessions = sessionize(events, gap_minutes=settings.session_gap_minutes)
    transitions = transitions_from_sessions(sessions)
    diversity = compute_diversity(events, transitions)
    temporal = compute_temporal(events)
    play_counts = Counter(event.artist_id for event in events)
    names = {event.artist_id: event.artist_name for event in events}
    graph = build_transition_graph(transitions, dict(play_counts), names)
    insights = overview_insights(events, transitions, user.display_name)
    clusters = cluster_artists(events)
    recommendations = recommend_revisits(events, transitions)
    personas = synthetic_personas(db) if user.is_demo else {}
    similarity = compare_users(events, personas) if personas else []

    top_artists = [
        {"id": artist_id, "name": names[artist_id], "plays": count, "share": round(count / len(events), 4)}
        for artist_id, count in play_counts.most_common(12)
    ] if events else []

    strongest = next((edge for edge in transitions if edge.source_artist_id != edge.target_artist_id), None)

    return {
        "user": {
            "id": user.id,
            "display_name": user.display_name,
            "is_demo": user.is_demo,
            "image_url": user.image_url,
        },
        "overview": {
            **insights,
            "plays": len(events),
            "unique_artists": diversity.unique_artists,
            "unique_tracks": diversity.unique_tracks,
            "session_count": len(sessions),
            "top_artist": top_artists[0] if top_artists else None,
            "strongest_transition": (
                {
                    "source": strongest.source_artist_name,
                    "target": strongest.target_artist_name,
                    "count": strongest.count,
                    "probability": round(strongest.probability, 4),
                }
                if strongest
                else None
            ),
            "diversity_score": diversity.normalized_entropy,
            "diversity_interpretation": diversity.interpretation,
        },
        "evolution": {
            "weekly": weekly_evolution(events),
            "rising": insights.get("rising") or [],
        },
        "network": {
            "insight": graph.insight,
            "nodes": [node.__dict__ for node in graph.nodes],
            "edges": graph.edges,
            "transitions": [
                {
                    "source_id": edge.source_artist_id,
                    "target_id": edge.target_artist_id,
                    "source": edge.source_artist_name,
                    "target": edge.target_artist_name,
                    "count": edge.count,
                    "probability": round(edge.probability, 4),
                }
                for edge in transitions[:40]
                if edge.source_artist_id != edge.target_artist_id
            ],
        },
        "patterns": {
            "hours": temporal.hours,
            "hour_buckets": [_asdict_bucket(item) for item in temporal.hour_buckets],
            "weekdays": [_asdict_bucket(item) for item in temporal.weekdays],
            "months": [_asdict_bucket(item) for item in temporal.months],
            "seasons": [_asdict_bucket(item) for item in temporal.seasons],
            "peak_hour_insight": temporal.peak_hour_insight,
            "peak_weekday_insight": temporal.peak_weekday_insight,
            "peak_hour": temporal.peak_hour,
            "peak_weekday": temporal.peak_weekday,
        },
        "taste": {
            "diversity": diversity.__dict__,
            "top_artists": top_artists,
            "clusters": [cluster.__dict__ for cluster in clusters],
            "similarity": similarity,
        },
        "recommendations": [item.__dict__ for item in recommendations],
        "sessions": [
            {
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat(),
                "track_count": session.track_count,
                "unique_artists": session.unique_artist_count,
                "dominant_artist": session.dominant_artist_name,
                "dominant_genre": session.dominant_genre,
                "duration_seconds": session.duration_seconds,
            }
            for session in sessions[-12:]
        ],
    }
