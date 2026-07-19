# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeCheck 1.0**

Every recommendation it makes comes with a "because" line, so you can always see why a song
was picked.

---

## 2. Intended Use

### What it is for

VibeCheck suggests songs from a small collection based on what a listener says they like.
You describe your taste in four ways: a genre, a mood, how energetic you want the music, and
how upbeat or gloomy you want it to feel. It then ranks every song and shows you the best
five, along with the reason each one was chosen.

It was built for a class project. The point is to show how a recommender turns data into
suggestions, and to make the reasoning visible instead of hiding it.

### What it assumes about you

It assumes you can describe your taste in words, that your taste is one consistent thing
rather than several moods, and that you want more of what you already like. All three
assumptions are wrong for real people, which is part of what makes it interesting to study.

### What it should not be used for

- **Real listeners on a real service.** It has 20 songs and no idea what anyone actually
  played.
- **Deciding which artists get promoted.** Some songs in my own collection can never be
  recommended at all. Using this to decide who gets heard would quietly bury them.
- **Any claim that it knows what is good.** It measures similarity to a description. It has
  no opinion about quality.
- **Anything where being confidently wrong matters.** It never signals when it is unsure.

---

## 3. How the Model Works

Think of it as a judge giving each song a score out of 5.5 points.

Every song gets points for four things:

- **Genre** — up to 2 points. Full marks if the genre matches exactly. Half marks if the two
  genres share a word, so someone who likes "pop" gets partial credit for "indie pop".
- **Mood** — 1.5 points if the mood matches exactly, nothing otherwise.
- **Energy** — up to 1 point, based on how close the song is to the energy you asked for.
- **Positivity** — up to 1 point, based on how close the song is to the mood level you asked
  for, from gloomy to cheerful.

The important idea with the last two is that **closer is better, not higher**. If you ask for
calm music, a loud song loses points for being loud. A lot of simple recommenders get this
wrong and just hand you the loudest song every time.

Once every song has a score, they are sorted from best to worst and the top five are shown.
Sorting is a separate step from scoring on purpose. Some decisions can only be made by looking
at the whole list — like not showing you two songs by the same artist — and you cannot make
those while judging one song alone.

### What I changed from the starter

- I added **positivity** as a fourth measure. The starter only looked at energy, which tells
  you how loud a song is but not how it feels. Without it, someone asking for dark, heavy
  music was offered a cheerful gym anthem.
- I ignored three measures that came with the data — tempo, danceability, and how acoustic a
  song is. I checked, and they mostly repeat what energy already tells you. Counting them
  would have secretly made loudness four times more important than genre.
- I made the sorting break ties deliberately. Otherwise two equally good songs are ordered by
  whichever one I happened to type into the spreadsheet first.

### Extras added later

Three optional things sit on top of the four measures above. All are **off unless asked for**,
so the results in section 7 are exactly what the basic version produces.

- **Five more attributes** a listener can ask about: detailed mood tags, popularity, decade,
  how much singing there is, and language. Each adds its own points, and the maximum possible
  score rises to match, so a listener who fills in more preferences is still judged fairly.
- **A diversity penalty** that takes points off a song for each already-chosen song sharing
  its artist or genre. Explained in section 6.
- **A table view** of the results, so the reasons sit next to the scores instead of below them.

---

## 4. Data

The collection has **20 songs** in a spreadsheet file. The starter came with 10 and I wrote
10 more.

Each song has 15 pieces of information. The songs and artists are invented, not real.

| What it records | Column | Range |
|---|---|---|
| Identity | `id`, `title`, `artist` | text |
| Style | `genre`, `mood` | text |
| Sound | `energy`, `valence`, `danceability`, `acousticness` | 0.0 – 1.0 |
| Speed | `tempo_bpm` | 58 – 152 |
| How well known | `popularity` | 0 – 100 |
| Era | `release_decade` | 1990 – 2020 |
| Singing vs instrumental | `vocal_presence` | 0.0 – 1.0 |
| Detailed feelings | `mood_tags` | three tags per song |
| Language | `language` | english, spanish, instrumental |

There are 14 genres and 14 moods. Nine of the genres have only one song.

### What I added and why

The original 10 songs had a hidden problem. Every loud song was electronic, and every quiet
song was acoustic — with no exceptions. Real music is not like that. So I deliberately wrote
songs that break the pattern: a folk song that is loud and strummed, a quiet song made
entirely on a computer, and a metal song that is slow but crushing.

I also added genuinely sad music. The starter's gloomiest song was only neutral, so a listener
asking for melancholy music could not actually be served.

Later I added the last five columns in the table above. The one that mattered most was
`mood_tags`, because letting a song carry several feelings at once is what finally fixed the
worst bug in the system (see section 6). When I added them I checked whether they were
genuinely new information rather than repeats of what I already had — `popularity` initially
correlated with energy at +0.66, so I rewrote those values until it dropped to +0.30.

### What is missing

Plenty. There are no lyrics, so nothing knows what a song is actually about. Nothing records
whether you grew up with a song, and familiarity is a huge part of why people love music.
Only two languages appear, and one of those is really "no words at all". Whole traditions are
absent: no country, no reggae, no hip-hop beyond two tracks, nothing from outside Europe and
the Americas. With 20 songs, most genres have one or two examples, so "the best jazz song for
you" really means "the only jazz song."

---

## 5. Strengths

**It works well for listeners with clear, specific taste.** When someone asks for something
the collection actually contains, the results are good. The chill lofi listener got a perfect
match — a song that hit every single thing they asked for.

**It gives different people different music.** I tested six listeners and all six got a
different song in first place. That is the basic test of whether a recommender is listening at
all, and it passed.

**It explains itself.** Every recommendation shows what earned points and how many. If a
result looks wrong, you can see exactly why it happened rather than guessing. This turned out
to matter more than I expected — it is how I found most of the problems in section 6.

**It handles nonsense without breaking.** Asking for a genre that does not exist gives
sensible music rather than an error or an empty list.

**Closeness scoring behaves the way people actually talk.** When someone says "I want
something calm," they mean calm — not "as little energy as possible." Scoring by distance to
a target captures that, and it is the part of the design I am most confident was right.

---

## 6. Limitations and Bias

### The main weakness: mood words are compared as strings, not as meanings

The biggest flaw I found is that the system checks whether two mood labels are the *same
word*, not whether they mean the same thing. When I asked it for intense rock at a low
valence — dark, heavy music — it returned *Gym Hero*, a bright major-key pop workout track,
at #2, and buried *Iron Verdict* at #5, even though *Iron Verdict* is the most intense song
in the catalog and almost exactly what I described. *Iron Verdict* lost because its mood is
labelled `angry` while I typed `intense`, so it scored zero on the mood term while *Gym Hero*
collected the full 1.5 points for matching the word. I then tried to fix this by re-tuning
the weights, and discovered that **no weight can fix it**: a zero multiplied by any number is
still zero, so I could set the mood weight to 100 and *Iron Verdict* would gain nothing. This
matters beyond one song, because the catalog's 14 mood labels really describe about four
underlying feelings — `angry`/`intense`/`tense`, `chill`/`relaxed`/`focused`,
`happy`/`euphoric`/`hopeful`, and `melancholy`/`moody`/`nostalgic` — and exact matching
splinters each cluster into unrelated pieces.

### Other biases I found

**Partial genre credit only works for genres spelled with a space.** I added a rule giving
half credit when two genres share a word, so a `pop` fan gets credit for `indie pop`. But it
splits labels on spaces, which means:

```
user "pop"      vs song "indie pop"  -> 0.5   credit given
user "hip hop"  vs song "hip-hop"    -> 0.0   no credit
user "r and b"  vs song "r&b"        -> 0.0   no credit
```

A hip-hop fan who types the genre the normal way gets nothing, purely because the dataset
happens to hyphenate it. The benefit of my own fairness rule is decided by punctuation, which
is not a musical property at all.

**15% of the catalog can never be recommended.** Across all six profiles I tested,
*Grandmother's Hands*, *Saltwater Vows*, and *Slow Burn Letter* never appeared in a single
top-5. Nothing is broken — no profile asked for folk or r&b, so their genre term never fired.
But a purely content-based system has no way to surface a song nobody explicitly asks for. It
cannot say "people who liked what you liked also liked this," so unrequested music is simply
invisible. At the scale of a real platform, this is the mechanism that buries the long tail.

**Most genres have only one song, so recommendations quietly become padding.** Nine of the
14 genres have exactly one track. A metal fan gets one real match and then four songs that
merely happened to score highest among the leftovers. The output looks identical either way —
score 5.45 and score 1.59 are printed in the same format, so **the system never signals when
it is reaching**, and a user cannot tell a confident recommendation from a desperate one.

**Listeners with middle-of-the-road taste get near-random results.** Because closeness is
symmetric, a target in the middle of the range is equidistant from both extremes and cannot
prefer either. A profile asking for energy 0.65 and valence 0.50 produced a top five spanning
0.30 points — effectively a five-way tie ordered by tie-break rules rather than by taste. The
system serves people with strong, edge-of-the-range preferences well and people with moderate
taste poorly.

**It is a filter bubble by construction.** Being purely content-based, it can only recommend
things resembling what the user already said they like. It has no mechanism for a pleasant
surprise, no notion of discovery, and no way to represent multi-modal taste — the same person
wanting intense rock at the gym and chill lofi while studying cannot be expressed. Asking for
the midpoint does not return both; it returns the mediocre middle.

### The most important fix

Give moods the same partial credit that genres already get, using synonym clusters rather
than exact strings. This is the one change with direct evidence behind it: it is the only fix
that would move *Iron Verdict* to where it belongs, and no amount of weight tuning can
substitute for it.

---

### A fairness feature I added: the diversity penalty

Two of the problems above — a small number of songs taking every slot, and 15% of the
collection being unreachable — come from the same cause. Ranking purely by score means the
best-matching songs win *every* position, even when they are nearly the same song.

So I added a rule that subtracts points from a song for each song **already chosen** that
shares its artist or its genre. The important detail is "already chosen": the penalty depends
on what is above it in the list, so it cannot be part of a song's own score. It has to live in
the ranking step. This is the clearest example of why scoring and ranking are separate.

Here is the same listener at three settings:

```
OFF (default)
   5.50  Library Rain          Paper Lanterns  lofi
   5.46  Midnight Coding       LoRoom          lofi
   3.98  Focus Flow            LoRoom          lofi
   3.42  Spacewalk Thoughts    Orbit Bloom     ambient
   1.87  Coffee Shop Stories   Slow Stereo     jazz

ARTIST PENALTY 1.0
   5.50  Library Rain          Paper Lanterns  lofi
   5.46  Midnight Coding       LoRoom          lofi
   3.42  Spacewalk Thoughts    Orbit Bloom     ambient
   2.98  Focus Flow            LoRoom          lofi     <- LoRoom's second song, demoted
   1.87  Coffee Shop Stories   Slow Stereo     jazz

ARTIST PENALTY 1.0 + GENRE PENALTY 0.8
   5.50  Library Rain          Paper Lanterns  lofi
   4.66  Midnight Coding       LoRoom          lofi
   3.42  Spacewalk Thoughts    Orbit Bloom     ambient
   1.87  Coffee Shop Stories   Slow Stereo     jazz
   1.78  Saltwater Vows        Amaya Cruz      r&b      <- previously unreachable
```

**How this improves fairness.** With the penalty off, the top three are all lofi and two are
by the same artist. Turning on the artist penalty pushes LoRoom's second song below a
different artist who scored lower — the listener still gets it, just not twice in a row.
Adding the genre penalty goes further and surfaces *Saltwater Vows*, which is one of the three
songs that had **never appeared for any of the six listeners I tested**. A song that was
effectively invisible became reachable.

That is the fairness argument in a sentence: without this, being slightly worse on score means
never being heard at all, no matter how many people are listening. The penalty changes the
question from "which songs match best" to "which songs match best *that I have not already
said*".

**What it costs.** This is a genuine trade-off, not a free improvement. Every song promoted by
the penalty is, by definition, a worse match than the one it displaced — *Saltwater Vows* at
1.78 is not what a lofi listener asked for. Pushed too hard, the rule stops serving the
listener in order to serve the catalog. That is why it is **off by default** and set per
request rather than baked into the score: it is a decision about what a list is *for*, and
that is not something a scoring function should quietly decide on everyone's behalf.

---

## 7. Evaluation

### Who I tested with

I made up six imaginary listeners. Three of them are ordinary music fans:

- **High-Energy Pop** — wants cheerful, upbeat pop
- **Chill Lofi** — wants quiet background music for studying
- **Deep Intense Rock** — wants loud, heavy, dark music

The other three were designed to trip the system up rather than to be served well:

- **Contradictory** — asks for classical music but also wants it very loud, which nothing in
  the collection actually is
- **Indecisive** — names no genre and no mood, and asks for everything in the middle
- **Unknown genre** — asks for k-pop, which isn't in the collection at all

The first thing I checked was simple: do these six people get different music? If everyone
gets roughly the same songs, the system isn't really listening to anyone. They didn't —
**all six got a different song in first place**, and 17 of the 20 songs turned up somewhere.

### Comparing the profiles, two at a time

**Pop vs Lofi — the clearest success.** These two lists have nothing in common. The pop fan
gets bright, fast, cheerful songs; the lofi fan gets quiet, slow, calm ones. That makes sense,
because the two listeners asked for opposite things on every single measure — different genre,
different mood, and energy of 0.80 versus 0.35. When two people describe opposite tastes and
get opposite music, the system is working. The lofi fan also got the only flawless result in
the whole experiment: *Library Rain* matched their request perfectly on every count.

**Pop vs Rock — same loudness, very different feel.** Both listeners want energetic music, so
you might expect similar results, and they do share one song. But the pop fan's list is
cheerful and the rock fan's is dark, and that difference comes almost entirely from one
number: how positive or negative a song sounds. The pop fan asked for 0.75 on that scale and
the rock fan asked for 0.40. That single number is what separates a gym anthem from a storm
track even when both are equally loud, and it's the main reason I added it to the system in
the first place.

**Lofi vs Rock — opposite ends of everything.** As expected, these two share no songs at all.
The interesting part is *how* they fail at the bottom. Both lists run out of genuinely good
matches after three or four songs, and then start including songs that fit only loosely. The
lofi fan ends up with a jazz track and the rock fan ends up with a synthwave one — neither is
wrong exactly, but neither was really asked for. Both listeners hit the same wall: the
collection is small, and once the right songs are used up, the system keeps going anyway.

**The three edge cases.** The contradictory listener asked for loud classical music and was
handed **metal**. I actually think that was the sensible choice — it went with the *sound*
they described rather than the *label* they typed — but it never mentioned that their request
was impossible. The indecisive listener got five songs whose scores were almost identical, so
the order was essentially arbitrary. And the k-pop listener got reasonable upbeat pop rather
than an error, which is the right way to fail.

### What surprised me

**The weights matter far less than I assumed.** I halved the importance of genre and doubled
the importance of energy, expecting the recommendations to change a lot. The exact same five
songs came back for every listener. Only their order shifted, and the top song never changed
once. Genre sorts songs into rough groups, and the other measures only shuffle songs within
those groups.

**A bad recommendation looked exactly like a good one.** The system scores its answers, and
those scores range from 5.50 (perfect) down to 1.59 (barely relevant). But it prints both the
same way, with the same confidence. It has the information needed to say "I'm not sure about
this one" and never does.

**Some songs are invisible.** Three songs never appeared for any of the six listeners. They
aren't bad songs — nobody happened to ask for folk or r&b, and this kind of system can only
offer you things you've already described.

### Why "Gym Hero" keeps turning up for people who want happy pop

*Gym Hero* is a workout song — the kind of thing you'd play while lifting weights. It is
filed under **pop**, it's very loud, and it sounds bright rather than gloomy. Someone asking
for happy pop is asking for three things: the pop label, a happy feeling, and reasonably
upbeat energy. *Gym Hero* clearly has two of those three.

The trouble is how the system adds up its points. A matching genre label is worth 2 points —
the largest single award — and a matching mood is worth only 1.5. *Gym Hero* is tagged
`intense`, not `happy`, so it earns nothing for mood. But it collects the full 2 points just
for being pop, plus nearly full marks for loudness and brightness, and that's enough to place
it third.

Meanwhile *Late Bus Freestyle*, which genuinely is a happy song, ranks below it — because it's
hip-hop rather than pop, and it loses the big 2-point genre award. **So a song with the right
label but the wrong feeling beat a song with the right feeling but the wrong label.**

To a person this looks silly. Nobody asks for happy music and means "anything filed under pop
will do." But the system has no idea what these words mean; it only knows that "pop" is worth
more points than "happy". When I later halved the genre award, the happy song moved above the
workout song — which tells me the ordering was never about the music. It was about which
label I decided was worth more.

---

## 8. Ideas for Improvement

**1. Teach it that moods can be synonyms.** This is the most important fix. Right now `angry`
and `intense` are treated as completely unrelated words, which is why the heaviest song in the
collection was ranked fifth for a listener who wanted heavy music. Grouping moods that mean
roughly the same thing would fix it. I know weight tuning cannot, because I tried — a song
scoring zero on mood stays at zero no matter how much the mood is worth.

**2. Let it say when it is unsure.** The system already knows the difference between a great
match and a weak one — 5.50 versus 1.59 — but prints both identically. It should stop early
when nothing scores well, or at least label the weak ones. Right now it pads the list to five
songs and says nothing about it, which makes a desperate guess look like a confident pick.

**3. Let people like more than one thing.** A listener can currently describe only one taste.
Real people want loud music at the gym and quiet music while studying, and asking for the
average of those gets you neither. Allowing several genres or moods per person would fix this,
and it is a small change.

Two smaller ones I would also do: compare genres in a way that is not confused by punctuation
(a "hip hop" fan currently gets nothing for "hip-hop"), and add an artist limit so the same
artist cannot take several spots in one list.

---

## 9. Personal Reflection

The thing that surprised me most was how little the weights mattered. I spent real effort
deciding whether genre should be worth 2 points and mood 1.5. Then I halved one and doubled
another, and the same five songs came back for every listener — only their order moved. I had
assumed tuning those numbers was the main job. It turned out the numbers mostly rearranged
songs that were already going to be recommended.

What actually decided the results was much less glamorous: whether two words matched exactly.
The worst mistake in my system was not a bad weight, it was that `angry` and `intense` are
different strings. A computer sees no relationship there at all, and no amount of tuning fixes
it. That reframed the whole project for me — the interesting decisions were about how things
get compared, not how much they get multiplied by.

I also learned that a system can be wrong and confident at the same time, and that this is the
default rather than an unusual failure. My recommender never once said "I am not sure." It
handed over a barely-relevant song in exactly the same format as a perfect one. Nothing was
broken; it simply had no way to express doubt unless I built one.

It has changed how I read my own recommendations. When an app suggests something odd, I no
longer assume it knows something I do not. It is far more likely that it matched a label
rather than the music, or that it ran out of good options and kept going anyway. I am also
more aware that the songs I never get shown are a real thing — three songs in my own tiny
collection could not be recommended to anyone, and I only found out because I went looking.
