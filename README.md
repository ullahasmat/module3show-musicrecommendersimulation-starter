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

### What my version prioritizes

I score each song on four things: **genre, mood, energy, and valence.** I deliberately left
out `tempo_bpm`, `danceability`, and `acousticness` even though they're in the dataset.
When I checked how the columns relate to each other, those three turned out to track energy
almost exactly (acousticness moves opposite to energy at a correlation of −0.99). They
aren't extra information — they're the same "how intense is this song" signal repeated.
Scoring all of them would have quietly weighted intensity about four times heavier than
genre without that showing up anywhere in the code. Valence is the one number that behaves
independently, so it's the one that actually adds something: it separates *Storm Runner*
(intense and dark) from *Gym Hero* (intense and upbeat), which have nearly identical energy
but feel nothing alike.

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
| `tempo_bpm` | 60–152 | ❌ correlates 0.96 with energy |
| `danceability` | 0.0–1.0 | ❌ correlates 0.86 with energy |
| `acousticness` | 0.0–1.0 | ❌ correlates −0.99 with energy |

**`UserProfile`**

| Field | Meaning |
|---|---|
| `favorite_genre` | Genre to match, e.g. `"pop"` |
| `favorite_mood` | Mood to match, e.g. `"happy"` |
| `target_energy` | Desired intensity, 0.0–1.0 — matched by closeness, not "higher is better" |
| `target_valence` | Desired positivity, 0.0–1.0 — matched by closeness |
| `likes_acoustic` | Kept for compatibility, but barely usable (see note below) |

### Scoring and ranking

I split this into two separate rules, because they answer different questions.

The **scoring rule** looks at one song at a time and asks "how well does this fit?":

```
score = 2.0 × genre match      (1.0 exact, 0.5 partial like "pop" vs "indie pop", else 0)
      + 1.5 × mood match       (1.0 if equal, else 0)
      + 1.0 × energy closeness
      + 1.0 × valence closeness
                                                     maximum possible = 5.5
```

The **ranking rule** takes all those scores and decides what to actually show: sort
descending, break ties on purpose, optionally limit one song per artist, and cut to the top
k.

I needed both because some decisions are impossible to make one song at a time. Whether to
show a second Neon Echo track depends on whether the first one is already in the list, and
the scoring function only ever sees one song, so it can't know that. Ties matter too — two
lofi songs scored 5.4841 and 5.4802 for one of my test profiles, a gap that's basically
noise, and if I don't break that tie deliberately Python just falls back to the order the
rows appear in the CSV. Scoring measures merit; ranking decides policy.

### Known quirk in the profile

`target_energy` and `likes_acoustic` are almost the same setting in this dataset, since
energy and acousticness are correlated at −0.99. No song in the catalog is both high-energy
and highly acoustic, so a profile asking for `target_energy=0.9` **and** `likes_acoustic=True`
is asking for something that doesn't exist, and will get results matching neither. I'll come
back to this in the model card.

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

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

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



