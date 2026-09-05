# Analytics methodology

## Sessionization

Listening events are ordered by `played_at`. A new session starts when the gap
between consecutive events is **strictly greater than** `SESSION_GAP_MINUTES`
(default 30). A gap equal to the threshold remains in the current session.

This is a heuristic, not a Spotify-provided session object.

## Artist transitions

Inside a session, consecutive plays define a directed edge from the primary
artist of track *n* to the primary artist of track *n+1*.

```
P(B | A) = count(A → B) / Σ count(A → *)
```

Self-transitions (A → A) are stored because repeat listening is real, but the
default network visualization hides them so the graph stays readable.

## Graph

NetworkX builds a directed weighted graph on the filtered edge set (minimum
count, capped edge count, optional focus artist). PageRank uses edge weight.
Hub highlighting uses degree. The default view is the strongest edges, not the
full spaghetti of every handoff.

## Diversity

| Metric | Meaning |
| --- | --- |
| Artist entropy | H = −Σ pᵢ log₂(pᵢ) over artist play shares |
| Normalized entropy | H / log₂(n). 1 is even; 0 is a single artist |
| Herfindahl index | Σ pᵢ². Higher is more concentrated |
| Top-artist share | Plays of the #1 artist / all plays |
| Repeat rate | 1 − unique tracks / plays |

These describe mix concentration, not personality.

## Clustering

Artist vectors use **behavioral statistics from the user’s own events**: play
share, weekend share, hour-of-day mix, monthly mix. Features are standardized,
then K-means with a small k chosen from artist count. Cluster titles are
playful UI labels, not scientific identities.

Spotify audio features, audio analysis, and the recommendations endpoint are
not used. No model is trained on Spotify catalog audio.

## Recommendations

A transparent heuristic:

```
score = 0.45 × historical share
      + 0.35 × recency-gap × share
      + 0.20 × neighbor pull
```

Neighbor pull rewards artists often reached from artists that are still active,
when the candidate itself has gone quiet. Each card explains the reason.

## Similarity

Cosine similarity of artist-share vectors. The demo compares against synthetic
personas. This is “similar listening patterns,” not “similar people.”

## Discover: similar tracks and A→B bridges

These tools do **not** use `/recommendations`, audio features, audio analysis,
or related-artists.

**Neighbors.** Resolve a pasted `open.spotify.com/track/{id}` link (or a name)
via Get Track / Search. Rank: same artist, shared artist-genre tags, then
artists that appear next to the seed in *your* session graph.

**Bridge.** Treat artists as a graph: catalog follow-edges, shared genres, and
your handoffs. Take a shortest path from the opening artist to the destination
artist and pick one track per hop. That is “flow” as artist adjacency, not as
BPM.

Live catalog lookup uses your OAuth token when connected, or client credentials
if `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are set. Demo mode also
works entirely on the local catalog.

## Spotify API honesty

Recently played is a short window. Top artists/tracks are stored as **taste
snapshots**, never rewritten as extra play events. Demo mode exists so the
graph, sessions, and temporal views can be evaluated with a full synthetic
timeline.
