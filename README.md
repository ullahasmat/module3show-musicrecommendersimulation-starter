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

I ran the recommender against six profiles: three ordinary listeners, and three built
specifically to break it. All six run every time with `python -m src.main`.

### Profile 1 — High-Energy Pop

```
Your taste profile:
    genre            pop
    mood             happy
    target_energy    0.80
    target_valence   0.75

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

### Profile 2 — Chill Lofi

```
Your taste profile:
    genre            lofi
    mood             chill
    target_energy    0.35
    target_valence   0.58

1. Library Rain - Paper Lanterns
   score 5.50 / 5.50  [####################]
     - genre match: lofi (+2.00)
     - mood match: chill (+1.50)
     - energy 0.35 close to your 0.35 (+1.00)

2. Midnight Coding - LoRoom
   score 5.46 / 5.50  [####################]
     - genre match: lofi (+2.00)
     - mood match: chill (+1.50)
     - energy 0.42 close to your 0.35 (+0.96)

3. Focus Flow - LoRoom
   score 3.98 / 5.50  [##############......]
     - genre match: lofi (+2.00)
     - energy 0.40 close to your 0.35 (+0.98)
     - valence 0.59 close to your 0.58 (+1.00)

4. Spacewalk Thoughts - Orbit Bloom
   score 3.42 / 5.50  [############........]
     - mood match: chill (+1.50)
     - energy 0.28 close to your 0.35 (+0.96)
     - valence 0.65 close to your 0.58 (+0.96)

5. Coffee Shop Stories - Slow Stereo
   score 1.87 / 5.50  [#######.............]
     - energy 0.37 close to your 0.35 (+1.00)
     - valence 0.71 close to your 0.58 (+0.87)
```

### Profile 3 — Deep Intense Rock

```
Your taste profile:
    genre            rock
    mood             intense
    target_energy    0.92
    target_valence   0.40

1. Storm Runner - Voltline
   score 5.45 / 5.50  [####################]
     - genre match: rock (+2.00)
     - mood match: intense (+1.50)
     - energy 0.91 close to your 0.92 (+1.00)

2. Gym Hero - Max Pulse
   score 2.83 / 5.50  [##########..........]
     - mood match: intense (+1.50)
     - energy 0.93 close to your 0.92 (+1.00)
     - valence 0.77 far from your 0.40 (+0.33)

3. Concrete Garden - Tunnel Verse
   score 1.85 / 5.50  [#######.............]
     - energy 0.78 close to your 0.92 (+0.85)
     - valence 0.42 close to your 0.40 (+1.00)

4. Night Drive Loop - Neon Echo
   score 1.73 / 5.50  [######..............]
     - energy 0.75 close to your 0.92 (+0.79)
     - valence 0.49 close to your 0.40 (+0.94)

5. Iron Verdict - Ashfall Kin
   score 1.59 / 5.50  [######..............]
     - energy 0.97 close to your 0.92 (+0.98)
     - valence 0.15 somewhat near your 0.40 (+0.61)
```

### How the three compare

The three lists share **almost nothing**, which is the first thing worth checking — a
recommender that returns similar songs regardless of who is asking isn't recommending, it's
just reporting which songs are generically popular. Each profile got its own genre's songs at
the top, each #1 scored above 5.4 out of 5.5, and the only song appearing in two lists is
*Gym Hero*.

The **Chill Lofi** profile produced the only **perfect 5.50** in the whole experiment.
*Library Rain* is lofi, chill, and its energy is 0.35 against a target of 0.35 — an exact hit
on every term. Right behind it, *Midnight Coding* scored **5.46**. A 0.04 gap is not a real
preference, and this is exactly the tie the explicit tie-break rule exists for; without it,
CSV row order would have silently decided which one a user sees first.

Each list also shows the same **cliff** after the genuine matches run out — 3.35 to 1.76 for
pop, 3.42 to 1.87 for lofi, 2.83 to 1.85 for rock. Everything below the cliff is padding to
reach `k=5`, and nothing in the output says so.

### The rock profile exposes a real bug

Look at positions 2 and 5. A listener who asked for **intense music at valence 0.40** — dark,
heavy, aggressive — was given:

- **#2 *Gym Hero***, a bright major-key pop workout track at valence 0.77
- **#5 *Iron Verdict***, metal, valence 0.15, energy 0.97 — the single most intense song in
  the catalog and almost exactly what they described

*Iron Verdict* loses because its mood is labelled `angry` while the user typed `intense`.
Those are near-synonyms to any human, but exact string matching treats them as complete
strangers, so it forfeits the entire 1.5-point mood term. *Gym Hero* collects that 1.5 for
matching the word, and its badly wrong valence only costs it 0.67.

**A word mismatch outweighed being musically correct.** I flagged this risk in the plan
before writing the code — near-synonym moods scored as unrelated — but I did not expect it to
push the best answer down to fifth place. The fix is the same partial-credit idea already
used for genres (`pop` ~ `indie pop`), applied to moods.

### Edge case 1 — Contradictory profile

Asking for the `classical` genre and an energy of 0.95. Nothing in the catalog is both.

```
Your taste profile:
    genre            classical
    mood             angry
    target_energy    0.95
    target_valence   0.20

1. Iron Verdict - Ashfall Kin
   score 3.48 / 5.50  [#############.......]
     - mood match: angry (+1.50)
     - energy 0.97 close to your 0.95 (+1.00)
     - valence 0.15 close to your 0.20 (+0.98)

2. Nocturne in Grey - Elena Vasari
   score 2.92 / 5.50  [###########.........]
     - genre match: classical (+2.00)
     - energy 0.22 far from your 0.95 (+0.01)
     - valence 0.31 close to your 0.20 (+0.91)
```

Ask for loud classical music and you get **metal**. The one genuinely classical song is
second, and its energy term contributes **+0.01** — the Gaussian falloff is doing its job,
correctly ruling that 0.22 is nowhere near 0.95.

I actually think the system resolved this the *right* way: it decided the sound the listener
described mattered more than the label they typed. But it resolved a genuine contradiction
silently, and a user who sees "metal" at the top of a classical search has no way to know
their request was impossible. **The failure isn't the ranking, it's that nothing was said
about it.**

### Edge case 2 — Indecisive profile

No genre, no mood, and both numbers in the middle of the range.

```
Your taste profile:
    target_energy    0.65
    target_valence   0.50

1. Night Drive Loop - Neon Echo   score 1.92 / 5.50
2. Concrete Garden - Tunnel Verse score 1.82 / 5.50
3. Dust and Diesel - Hollis Ray   score 1.80 / 5.50
```

The top five span **0.30 points total**. That's not a ranking, it's a five-way tie with
decimals attached, and the ordering is effectively decided by the tie-break rules rather than
by taste. This confirms the prediction in the plan: because closeness is symmetric, a target
in the middle of the range is equidistant from both extremes and cannot prefer either.

**The system gives no signal that this happened.** Score 1.92 is printed with exactly the same
confidence as the 5.50 earlier — the numbers are far apart, but the presentation isn't.

### Edge case 3 — Unknown genre

A genre that simply does not exist in the catalog.

```
Your taste profile:
    genre            k-pop
    mood             happy
    target_energy    0.80
    target_valence   0.80

1. Rooftop Lights - Indigo Parade   score 3.49 / 5.50
2. Sunrise City - Neon Echo         score 3.48 / 5.50
3. Late Bus Freestyle - Tunnel Verse score 3.33 / 5.50
```

This one degrades gracefully — no crash, no empty list. With the genre term zeroed out for
every song, mood and the numbers take over and the results are reasonable upbeat pop, which is
a defensible answer for a k-pop fan.

Two things stand out. **#1 and #2 are 0.01 apart**, so the tie-break rule is effectively
choosing the top recommendation. And the order **flipped** relative to Profile 1 — with genre
removed, *Rooftop Lights* (valence 0.81) edges out *Sunrise City* (0.84) against the 0.80
target. Removing one term reshuffled the top, which is a reminder of how little separates
these two songs in the first place.

### Summary of what the experiments changed my mind about

| I expected | What actually happened |
|---|---|
| Genre would dominate everything | Genre sorts songs into tiers, but **mood word-matching** caused the worst error |
| The contradictory profile would produce nonsense | It resolved sensibly toward sound over label — it just never said so |
| Mid-range targets would be slightly vague | Discrimination collapsed to a 0.30 spread — effectively arbitrary |
| An unknown genre might break something | It degraded gracefully; the tie-break quietly picks the winner |

---

## Sensitivity Experiment: halving genre, doubling energy

I changed two weights at once — `W_GENRE` from 2.0 to 1.0 and `W_ENERGY` from 1.0 to 2.0 —
and re-ranked all three main profiles. The maximum possible score stays 5.5, so the numbers
are still directly comparable to the baseline.

```
=== High-Energy Pop ===
#   BASELINE g2.0 e1.0              EXPERIMENT g1.0 e2.0
1   Sunrise City (5.43)             Sunrise City (5.43)
2   Rooftop Lights (4.46)           Rooftop Lights (4.95)
3   Gym Hero (3.87)                 Late Bus Freestyle (4.21)    <-- CHANGED
4   Late Bus Freestyle (3.35)       Gym Hero (3.74)              <-- CHANGED
5   Fever Bloom (1.76)              Fever Bloom (2.71)

=== Chill Lofi ===
1   Library Rain (5.50)             Library Rain (5.50)
2   Midnight Coding (5.46)          Midnight Coding (5.42)
3   Focus Flow (3.98)               Spacewalk Thoughts (4.38)    <-- CHANGED
4   Spacewalk Thoughts (3.42)       Focus Flow (3.96)            <-- CHANGED
5   Coffee Shop Stories (1.87)      Coffee Shop Stories (2.87)

=== Deep Intense Rock ===
1   Storm Runner (5.45)             Storm Runner (5.45)
2   Gym Hero (2.83)                 Gym Hero (3.83)
3   Concrete Garden (1.85)          Concrete Garden (2.71)
4   Night Drive Loop (1.73)         Iron Verdict (2.57)          <-- CHANGED
5   Iron Verdict (1.59)             Night Drive Loop (2.52)      <-- CHANGED
```

### More accurate, or just different?

**Mostly just different — with one genuine improvement.**

The same five songs come back for every profile. Not one song entered or left any list; only
the order inside it moved, and **#1 never changed once**. Halving the heaviest weight in the
recipe and doubling another could not alter *which* songs get recommended. This matches what
I found when planning the recipe: the genre term sorts songs into coarse tiers (exact match /
partial / none) and the numeric terms only decide order *within* a tier. Changing the weights
stretches the scores without moving anything across a tier boundary.

**The one real improvement is in the pop list.** *Late Bus Freestyle* moved above *Gym Hero*.
That is the correct order and I said so before running this experiment: *Gym Hero* is pop but
its mood is `intense`, while *Late Bus Freestyle* actually matches the requested `happy`. With
genre at 2.0 the genre match outweighed the mood match; at 1.0 it no longer does. **Lowering
the genre weight fixed the genre-over-mood bias I predicted in the plan.**

The other movements are not improvements. *Spacewalk Thoughts* rising above *Focus Flow* for
the lofi listener is arguably worse — *Focus Flow* is actually lofi, *Spacewalk Thoughts* is
ambient, and the swap happens only because doubling energy rewards ambient's 0.28 against a
target of 0.35. That is the same genre-weakening that helped the pop list, hurting here.

### The finding that matters most

**No weight setting can fix the worst bug in the system.**

*Iron Verdict* rose one place, from #5 to #4, and is still below *Gym Hero* — a bright pop
track — for a listener who asked for dark intense music. It cannot rise further, because its
mood is labelled `angry` while the user typed `intense`, so its mood term is `1.5 x 0.0 = 0`.
**Zero multiplied by any weight is still zero.** I could set the mood weight to 100 and
*Iron Verdict* would gain nothing.

That reframes the whole experiment. The problem is not that the weights are tuned wrong — it
is that the *mood comparison itself* is wrong, treating near-synonyms as complete strangers.
Weight tuning is the wrong tool, and I would have spent a long time adjusting numbers without
ever fixing it. The real fix is partial credit for related moods, the same rule already
working for `pop` ~ `indie pop`.

I kept the original weights. The one improvement the change bought was real but narrow, it
made the lofi list slightly worse, and it left the actual defect untouched.

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

Full write-up of the system's limitations lives in the [**Model Card**](model_card.md). This
section is about the process of building it.

### My biggest learning moment

It was realising that my worst bug could not be fixed by tuning anything.

I had spent real effort choosing weights — genre worth 2 points, mood worth 1.5 — and treated
that as the main design work. Then I found the system ranking a bright pop workout track above
a metal song for a listener who explicitly asked for dark, heavy music. My instinct was to
adjust the weights. So I halved genre and doubled energy, and the wrong song moved up exactly
one place.

Then it clicked. The metal song scored **zero** on mood, because its label was `angry` and the
listener typed `intense`. Zero multiplied by any weight is still zero. I could have set the
mood weight to a hundred and changed nothing. **The bug was not in how much things counted, it
was in how things were compared.** I had been about to spend an afternoon tuning numbers that
could never have worked.

That reframed what I think the hard part of these systems actually is. Choosing weights feels
like the important decision because it involves numbers and judgement. But comparison rules —
what counts as a match at all — silently decide far more, and they are easy to write without
ever noticing you made a choice.

### How AI helped, and where I had to check it

The genuinely useful part was **analysis I would not have thought to run**. Asking it to check
how my song attributes related to each other revealed that energy, tempo, danceability and
acousticness were nearly the same measurement four times over — energy and acousticness moved
together at −0.99, essentially a straight line. I would have happily scored all four and
quietly made loudness four times more important than genre without ever seeing it in my own
code. It was also fast at running the same experiment across many profiles at once, which is
how the "three songs are never recommended" finding turned up.

Where I had to push back:

- **It let my documentation go stale.** Early on it wrote a −0.99 correlation into my README.
  Then I expanded the dataset from 10 songs to 20 and the real figure became −0.87. The README
  kept confidently stating the old number in three places. Nothing errored. Prose does not
  fail a test, so a document can become wrong while the code stays right — I now re-check any
  written claim after changing the data behind it.
- **It wrote an explanation that contradicted its own maths.** One output read
  `energy 0.97 far from your 0.80 (+0.79)` — "far from" next to a near-perfect score. The
  wording had been derived from one calculation and the number from another. It looked
  plausible enough that I nearly left it.
- **My tests passed for the wrong reason.** `pytest` reported 2 passed the whole way through,
  which felt like proof things worked. They were testing unimplemented placeholder methods and
  happened to pass because the test's first song was the right answer by luck. A green tick is
  not evidence.
- **A suggestion that would have made things worse.** When expanding the dataset, the obvious
  move was to add as many new genres as possible for variety. That would have left almost every
  genre with a single song, which turns the genre score into a filter rather than a ranking. I
  deliberately repeated genres instead.

The pattern I noticed: AI was strongest at things I could immediately verify — calculations,
running many cases, finding structure in data. It was least reliable at claims that stay true
only as long as something else does not change.

### What surprised me about how simple this is

There is no learning in this system at all. It is four multiplications and a sort. Nothing is
trained, nothing adapts, and it has never seen a single real listener.

And yet the output feels like a recommendation. When it returned a perfect 5.50 match for the
lofi listener, it genuinely looked like the system understood something about studying to
quiet music. It does not. It compared two words and measured two distances.

I think the feeling comes almost entirely from **the explanations and the ranking**, not the
intelligence. Sorting things and giving reasons is enough to read as judgement. That is a
slightly uncomfortable thing to learn, because it means a system can look thoughtful while
being arithmetic — and if this much conviction comes from four multiplications, I should be
much more careful about assuming a real recommender knows why it is suggesting something.

The flip side is that the reasons are also what exposed every flaw. Because the system had to
show its work, I could see the wrong song winning and understand why. A version that just
listed five songs would have looked fine.

### What I would try next

**Fix the mood comparison**, since it is the one thing with hard evidence behind it. Grouping
moods that mean roughly the same thing is a small change that moves a genuinely wrong result.

**Make it admit uncertainty.** The system already knows the difference between a 5.50 and a
1.59 and presents them identically. Stopping early instead of padding to five songs would be
more honest than any ranking improvement.

**Add a second ranking mode** — mood-first instead of genre-first — and compare them on the
same listener. Most of my findings came from running the same thing two ways and looking at
the difference, and that is the cheapest way to keep doing it.

If I had longer, the thing I would most want is data the system currently cannot see: whether
a listener skipped a song. Everything here is based on what someone *says* they like. Real
systems mostly learn from what people actually do, and the gap between those two is probably
where all the interesting behaviour lives.



