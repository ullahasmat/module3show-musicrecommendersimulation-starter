# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted.

---

## Agentic Workflow (SF8) — Adding advanced song attributes

### What task did I give the agent?

Add five new attributes to the dataset and wire them into the scoring, **without changing the
results of any profile I had already documented in the README**. That second half was the hard
part. My README contains scored output for six listeners, and if new attributes shifted those
numbers, every result I had written up would silently become wrong.

I also wanted the new attributes to carry genuinely new information. My earlier analysis had
shown that four of the original columns were nearly the same measurement repeated, and I did
not want to repeat that mistake with five more.

### Prompts used

> Add 5 new attributes to songs.csv: popularity 0-100, release decade, vocal presence 0-1,
> detailed mood tags, and language. Pick values that are NOT predictable from the columns I
> already have — I don't want another set of features that all track energy. Then update
> score_song so each new attribute only scores when the listener actually asks for it.

> The scoring says "max 5.5" everywhere. If a listener only fills in three preferences, is
> 5.5 still the right ceiling to compare against? Verify the maths is still valid.

> Before we finish: prove the four original profiles score exactly what they scored before
> this change. Show me the numbers, don't just tell me it's fine.

### What did the agent generate or change?

**`data/songs.csv`** — five new columns across all 20 rows: `popularity`, `release_decade`,
`vocal_presence`, `mood_tags` (several tags per song, separated by semicolons), and `language`.

**`src/recommender.py`**

- `LIST_FIELDS` so `mood_tags` is parsed into an actual list instead of one long string
- Five new scoring terms, each wrapped in a check so it only runs when the listener asked for
  that preference
- `TERM_WEIGHTS`, a table mapping each preference to what it is worth
- `max_score(user_prefs)`, which works out the ceiling for one specific profile

**`src/main.py`** — the score bar and the `x / y` display now use the profile's own ceiling,
plus three new demonstration profiles.

### What did I verify or fix manually?

**The ceiling was wrong, and I only caught it by asking.** The first version kept comparing
every score against the fixed 5.5. A listener who fills in three preferences can only ever
earn those three terms, so their perfect match would have displayed as something like
2.50 / 5.50 and looked mediocre. Nothing would have errored — the recommendations would have
been correctly *ordered* and misleadingly *labelled*. The fix was making the ceiling follow
the profile.

**Popularity would have silently scored zero for every song.** The closeness function expects
values between 0 and 1, but popularity runs 0 to 100. Comparing 88 against 30 on that scale
gives `exp(-26912)`, which is 0.0. Every song would have received exactly zero popularity
points, the term would have done nothing at all, and **nothing would have crashed or warned
me**. I found it by printing the raw term values rather than trusting the totals. The fix is
dividing both by 100 first.

**I insisted on a regression check instead of accepting reassurance.** I asked for the
original profiles to be re-scored and the numbers shown. They came back at 5.43 / 5.50,
5.50 / 5.50 and 5.45 / 5.50 — identical to what my README documents. Without that, I would
have been trusting a claim rather than evidence, and I had already been caught out earlier in
this project by documentation that quietly went stale after the data changed.

**I measured the new attributes instead of assuming they were independent — and had to fix
them.** The whole point was to add information the system did not already have, so I checked
how the new columns related to energy. Popularity came back at **+0.66**, meaning louder songs
were noticeably more likely to be popular. That is the exact flaw I had criticised in the
original data, reappearing in the data I had just written.

I fixed it by making the popularity values reflect how people actually listen: quiet lofi
study tracks stream enormously (*Midnight Coding* 80, *Focus Flow* 77), while rock and dance
are more niche now (*Storm Runner* 58, *Fever Bloom* 63). That dropped the correlation to
**+0.30**, which is a real relationship rather than a duplicate measurement.

| new attribute | correlation with energy |
|---|---|
| `popularity` | +0.30 (was +0.66 before I fixed it) |
| `release_decade` | +0.29 |
| `vocal_presence` | +0.49 |

The honest note is that I only caught this because I ran the check. Reading the file, the
first set of numbers looked perfectly reasonable.

### Did it work?

The `mood_tags` attribute fixed the worst bug in my recommender. Same listener, same request,
described two ways:

```
ASKED BY MOOD WORD ("intense")          ASKED BY MOOD TAGS ("intense", "aggressive")

1. Gym Hero        2.50 / 2.50          1. Storm Runner   2.50 / 2.50
2. Storm Runner    2.50 / 2.50          2. Iron Verdict   2.48 / 2.50
3. Fever Bloom     0.99 / 2.50          3. Gym Hero       1.00 / 2.50
```

On the left, a bright pop workout track is the top result for someone asking for dark, heavy
music, and *Iron Verdict* — the heaviest song in the collection — does not appear at all. On
the right it is second, and *Gym Hero* has correctly fallen to third because it has none of
the requested tags.

This is the fix I predicted in my model card but could not reach by tuning weights, because
*Iron Verdict* was scoring a literal zero on mood and zero times any weight is still zero.
Letting a song carry several mood tags is what actually solved it.

---

## Design Pattern (SF10)

> Not attempted.
