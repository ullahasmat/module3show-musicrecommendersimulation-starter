# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

### How real recommenders work

Platforms like Spotify and YouTube combine two different strategies. **Collaborative
filtering** ignores the music entirely and looks only at behavior: if lots of people who
played the songs I played also played some song I haven't heard, that song gets
recommended to me. It's powerful because it finds connections nobody could hand-label — a
bluegrass track and a hip-hop track can end up "similar" purely because the same listeners
play both. But it can't say anything about a song with no play history yet (the **cold
start problem**), and it tends to over-recommend already-popular songs.

**Content-based filtering** goes the other way and looks only at the song's own
attributes — genre, mood, tempo, energy — scoring each one against a profile of what the
listener already likes. It handles brand-new songs fine, since a song uploaded a minute ago
still has a tempo. Its weakness is the opposite one: it can only ever suggest more of what
you already listen to, which is how **filter bubbles** form.

Real systems run both, generate a few hundred candidates, and then hand them to a separate
**ranking** stage that reorders using context like time of day and recent skips, plus a
diversity pass so the final list isn't ten near-identical songs.

My simulation is **purely content-based**, because I only have song attributes and one
stated taste profile — there are no other users to learn from. So I expect to see the
content-based weaknesses show up clearly, especially the filter bubble.

### The dataset

I expanded `data/songs.csv` from the starter's 10 songs to **20**, adding ids 11–20.

The starter catalog had a problem I only found by checking how its columns related to each
other: `energy`, `tempo_bpm`, `danceability`, and `acousticness` were almost the same
number wearing four different labels. Energy and acousticness correlated at **−0.99**, which
is essentially a straight line — every loud song was electronic and every quiet song was
acoustic, with no exceptions. Real music isn't like that.

So I chose the new songs' values specifically to break that pattern. *Dust and Diesel* is
loud **and** acoustic (energy 0.61, acousticness 0.79) — a driving strummed folk track.
*Slow Burn Letter* is quiet **and** electronic (0.38 / 0.21). *Iron Verdict* is the most
intense song in the catalog at only 88 BPM, because slow and heavy is a real thing that the
starter's data said was impossible.

| correlation with `energy` | starter (10 songs) | expanded (20 songs) |
|---|---|---|
| `acousticness` | −0.99 | **−0.87** |
| `tempo_bpm` | 0.96 | **0.78** |
| `danceability` | 0.86 | **0.62** |

I also widened the valence range from `0.48–0.84` to **`0.15–0.91`**. The starter had no
genuinely sad music in it — the gloomiest track was merely neutral — so a user asking for
melancholy music couldn't actually be served.

On genres, I deliberately **repeated** rather than maximizing variety. Ten brand-new genres
would have meant one song per genre, which turns the genre weight into a filter instead of a
ranker. Instead the new songs cover six new genres with repeats (hip-hop ×2, folk ×2, r&b ×2,
plus metal, house, techno, classical). Two new artists also have two songs each, so artist
de-duplication has something real to act on.

### What my version prioritizes

I score each song on four things: **genre, mood, energy, and valence.** I deliberately left
out `tempo_bpm`, `danceability`, and `acousticness`. Even after expanding the dataset they
still track energy closely (see the table above), so they aren't extra information — they're
the same "how intense is this song" signal repeated. Scoring all of them would have quietly
weighted intensity about four times heavier than genre without that showing up anywhere in
the code. Valence is the one number that behaves independently, so it's the one that
actually adds something: it separates *Storm Runner* (intense and dark) from *Gym Hero*
(intense and upbeat), which have nearly identical energy but feel nothing alike.

For numeric features I score **closeness to what the user asked for**, not raw magnitude.
Adding `song.energy` straight into the score would just rank the loudest song first no
matter what the user wanted. Instead the score is highest when the song's value sits near
the user's target and falls off as it gets further away, so a user who wants calm music
gets calm music.

### Features used

**`Song`**

| Field | Type | Used in score? |
|---|---|---|
| `id`, `title`, `artist` | identity | No — display and artist de-duplication |
| `genre` | category | ✅ weight 2.0 |
| `mood` | category | ✅ weight 1.5 |
| `energy` | 0.0–1.0 | ✅ weight 1.0, closeness |
| `valence` | 0.0–1.0 | ✅ weight 1.0, closeness |
| `tempo_bpm` | 58–152 | ❌ correlates 0.78 with energy |
| `danceability` | 0.0–1.0 | ❌ correlates 0.62 with energy |
| `acousticness` | 0.0–1.0 | ❌ correlates −0.87 with energy |

**`UserProfile`**

| Field | Meaning |
|---|---|
| `favorite_genre` | Genre to match, e.g. `"pop"` |
| `favorite_mood` | Mood to match, e.g. `"happy"` |
| `target_energy` | Desired intensity, 0.0–1.0 — matched by closeness, not "higher is better" |
| `target_valence` | Desired positivity, 0.0–1.0 — matched by closeness |
| `likes_acoustic` | Kept for compatibility, but barely usable (see note below) |

The profile I'm testing with:

```python
user_prefs = {
    "genre":          "pop",
    "mood":           "happy",
    "target_energy":  0.80,
    "target_valence": 0.75,
}
```

I renamed the starter's `"energy"` key to `"target_energy"` on purpose. `energy` reads like
"this profile has energy 0.8"; `target_energy` says "aim for 0.8", which is what the scoring
actually does.

### The Algorithm Recipe

I split this into two separate rules, because they answer different questions.

```
SCORING RULE — score(user_prefs, song) -> (score, reasons[])

    2.0 × genre_match      1.0 exact | 0.5 shared word ("pop" ~ "indie pop") | 0.0 none
  + 1.5 × mood_match       1.0 if equal | 0.0 otherwise
  + 1.0 × closeness(song.energy,  user.target_energy)
  + 1.0 × closeness(song.valence, user.target_valence)
                                                            maximum = 5.5

  closeness(a, b) = exp(-(a - b)² / (2 × 0.25²))     Gaussian falloff, sigma = 0.25


RANKING RULE — recommend_songs(user_prefs, songs, k=5) -> [(song, score, explanation)]

  1. score every song in the catalog
  2. sort by score, descending
  3. break ties explicitly — closer energy first, then title
     (never let it fall through to CSV row order)
  4. optional: at most one song per artist          [diversity]
  5. return the top k
```

**Why Gaussian instead of `1 - |a - b|`.** With linear falloff, the *worst possible* energy
match in the catalog still earns about half credit, and enough near-misses stacked together
can outrank a real match. The Gaussian is forgiving of small misses and harsh on large ones,
which is what "close to what I asked for" actually means.

**Why closeness and not raw magnitude.** Adding `song.energy` straight into the score would
rank the loudest song first no matter what the user wanted. A user asking for calm music
should get calm music.

**Why two rules and not one.** Some decisions can't be made one song at a time. Whether to
show a second Neon Echo track depends on whether the first one is already in the list, and
the scoring function only ever sees one song, so it can't know that. Ties matter too — two
lofi songs scored 5.4841 and 5.4802 for one of my test profiles, a gap that's basically
noise, and if I don't break that tie deliberately Python falls back to the order the rows
happen to appear in the CSV. **Scoring measures merit; ranking decides policy.**

**Why mood is 1.5 and not the 1.0 I started with.** Honestly, on a 20-song catalog I can't
demonstrate that it matters — I tried both and the recommendations came out in the same
order. I kept 1.5 because a mood match feels like a stronger signal than a single numeric
feature, but it's a preference I haven't been able to prove.

### Biases I expect to see

I'm writing these down before implementing so I can check whether they actually show up.

**It will over-prioritize genre and miss good mood matches.** Genre is the heaviest term at
2.0, and because it's mostly all-or-nothing it sorts songs into tiers before anything else
gets a say. A jazz fan who wants relaxed music will likely get the one jazz song ranked
first, then whatever else is relaxed — but a genuinely perfect relaxed song in the "wrong"
genre has to overcome a 2.0-point deficit using terms worth 1.0 each. It probably can't.

**It will build a filter bubble.** This is the core weakness of content-based filtering and
I've designed it right in: the system can only recommend things resembling what the user
already said they like. It has no mechanism to introduce anything genuinely new, and no
concept of a pleasant surprise.

**Rare genres get squeezed.** Even after expanding the dataset, 14 genres across 20 songs
means most genres have only one or two songs. A metal fan runs out of real matches after one
song and the rest of the list is padding — songs that scored highest among the leftovers, not
songs that are actually good for them. The score won't warn anyone that this happened.

**Exact string matching treats near-synonyms as strangers.** `chill`, `relaxed`, and
`focused` are nearly the same mood, but a "chill" fan gets zero credit for a "relaxed" song.
I've added partial credit for multi-word genres (`pop` ~ `indie pop`) but there's no
equivalent for moods.

**A middle-of-the-road user gets close to random results.** Because closeness is symmetric, a
target sitting in the middle of the range is equidistant from both extremes and can't prefer
either. Testing `target_energy=0.65` scored chill lofi *higher* than intense rock — the
opposite of what that user probably wanted. The system only discriminates well when the
targets are near the edges.

**There's no way to express dislike, and no context.** The profile says what someone wants
but never what to avoid, and it has no idea whether it's 7am or 11pm. Real taste is
multi-modal — the same person wants intense rock at the gym and chill lofi while studying —
and a single point in taste space can't represent that. Asking for the midpoint doesn't give
you both; it gives you the mediocre middle.

### Known quirk in the profile

`target_energy` and `likes_acoustic` are nearly the same setting, since energy and
acousticness correlate at −0.87. No song in the catalog is both high-energy and highly
acoustic, so a profile asking for `target_energy=0.9` **and** `likes_acoustic=True` is asking
for something that doesn't exist, and will get results matching neither. I'll come back to
this in the model card.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Run with `python -m src.main` from the project root.

```
====================================================================
  MUSIC RECOMMENDER SIMULATION
====================================================================
Loaded songs: 20

Your taste profile:
    genre            pop
    mood             happy
    target_energy    0.80
    target_valence   0.75

--------------------------------------------------------------------
  Top 5 recommendations
--------------------------------------------------------------------

1. Sunrise City - Neon Echo
   score 5.43 / 5.50  [####################]
     - genre match: pop (+2.00)
     - mood match: happy (+1.50)
     - energy 0.82 close to your 0.80 (+1.00)

2. Rooftop Lights - Indigo Parade
   score 4.46 / 5.50  [################....]
     - related genre: indie pop ~ pop (+1.00)
     - mood match: happy (+1.50)
     - energy 0.76 close to your 0.80 (+0.99)

3. Gym Hero - Max Pulse
   score 3.87 / 5.50  [##############......]
     - genre match: pop (+2.00)
     - energy 0.93 close to your 0.80 (+0.87)
     - valence 0.77 close to your 0.75 (+1.00)

4. Late Bus Freestyle - Tunnel Verse
   score 3.35 / 5.50  [############........]
     - mood match: happy (+1.50)
     - energy 0.66 close to your 0.80 (+0.85)
     - valence 0.74 close to your 0.75 (+1.00)

5. Fever Bloom - Solaris Kite
   score 1.76 / 5.50  [######..............]
     - energy 0.88 close to your 0.80 (+0.95)
     - valence 0.91 close to your 0.75 (+0.81)
```

### Does this match what I expected?

Mostly yes, and the two places it surprised me are the interesting part.

**#1 is exactly right.** *Sunrise City* is pop, happy, energy 0.82 against a target of 0.80.
It scores 5.43 out of a possible 5.50, and the only reason it isn't perfect is that its
valence (0.84) sits slightly above what I asked for. That is the system working as designed.

**#2 proves the partial genre credit was worth adding.** *Rooftop Lights* is `indie pop`, not
`pop`, so plain string matching would have scored it a flat zero on the heaviest term in the
recipe. Instead it earns half credit and lands at #2, which is where a pop fan would
genuinely want it. Without that rule it would have dropped below songs that match nothing.

**#3 is where I disagree with my own system.** *Gym Hero* is pop with almost perfect energy
and valence, but its mood is `intense` — it's a gym track, not a happy one. It still beats
*Late Bus Freestyle*, which does match the requested mood, because a genre match (2.0) plus
strong numbers outweighs a mood match (1.5). **This is the genre-over-mood bias I predicted
in the plan, showing up in the very first run.** The system is behaving exactly as specified;
I'm just no longer sure the specification is right.

**#5 shows the catalog running dry.** Look at the gap between #4 (3.35) and #5 (1.76) — the
score nearly halves. *Fever Bloom* matches neither genre nor mood; it earns its place purely
by having roughly the right energy and valence. After four genuinely happy, upbeat songs are
exhausted, the recommender is padding the list to reach k=5. **It gives no warning that this
has happened** — the fifth slot looks the same as the first, just with a smaller number.
A real system would either stop early or admit it was reaching.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



