"""CP French — reading / decoding (lecture, décodage).

The most structuring domain for a school brain, and the one that best exposes
the difference between a *rule* and *memorisation*: decoding turns written words
into their phonological form by applying grapheme→phoneme correspondences (GPC)
and blending them into syllables. A reader who has the *skill* can decode words
— and even pseudo-words — never seen before; a memoriser cannot.

Three nodes, all fed through the ingestion contract:

* ``fr.CP.lecture_mots_reguliers`` — decode regular words by GPC + blending.
  Transfer is measured on unseen real words **and pseudo-words** (the gold
  standard for an alphabetic-decoding skill).
* ``fr.CP.lecture_mots_irreguliers`` — irregular / sight words where GPC gives
  the *wrong* reading (``femme`` → ``/fam/`` not ``/fɛm/``). They must be stored
  as wholes; over-applying GPC is the characteristic regularisation error.
* ``fr.CP.comprehension_phrase`` — answer a literal question about a simple
  sentence built from known words; role confusion is the characteristic error.

Phonemes use a compact ASCII code (not full IPA) — enough to make decoding
gradable and the errors diagnostic:
  vowels  a  e(é)  E(è/ɛ)  i  o  y(u)  U(ou)  Z9(eu)  @(e muet)
  nasals  AN(an)  ON(on)  IN(in)        glide  wa(oi)
  cons.   p b t d k g f v s z S(ch) Z(j) l R m n N(gn) ks(x)
"""
from __future__ import annotations

from dataclasses import dataclass

from .base import Task

SKILLS_LECTURE = [
    "grapheme_phoneme",      # apply a grapheme→phoneme correspondence
    "blending",              # fuse phonemes into syllables / a whole word
    "sight_words",           # recall an irregular word as a whole (orthographic lexicon)
    "lexical_access",        # map a decoded form to a known meaning
    "sentence_parsing",      # assign words to roles (who does what)
    "syllable_segmentation", # split a word into syllables
    "orthographic_encoding", # write a heard word (the inverse of decoding: dictée)
]

# ---- Grapheme → phoneme decoder --------------------------------------------
_VOWELS = set("aeiouyéèêàâ")
_FRONT = set("eiyéè")   # front vowels that soften c/g
_GFRONT = set("eiy")
_DIGRAPHS = [
    ("eau", "o"), ("ain", "IN"), ("ein", "IN"),
    ("ou", "U"), ("au", "o"), ("ai", "E"), ("ei", "E"), ("eu", "Z9"),
    ("on", "ON"), ("om", "ON"), ("an", "AN"), ("am", "AN"), ("en", "AN"), ("em", "AN"),
    ("in", "IN"), ("im", "IN"), ("ch", "S"), ("ph", "f"), ("gn", "N"), ("qu", "k"),
    ("oi", "wa"), ("ss", "s"), ("ll", "l"), ("tt", "t"), ("pp", "p"), ("mm", "m"),
    ("nn", "n"), ("rr", "R"),
]
_NASAL_G = {"an", "am", "en", "em", "on", "om", "in", "im", "ain", "ein"}
_SIMPLE = {"a": "a", "i": "i", "o": "o", "u": "y", "y": "i", "é": "e", "è": "E",
           "ê": "E", "à": "a", "â": "a", "p": "p", "b": "b", "t": "t", "d": "d",
           "f": "f", "v": "v", "z": "z", "l": "l", "m": "m", "n": "n", "r": "R",
           "j": "Z", "k": "k"}


def decode_gpc(word: str) -> str:
    """Competent basic decoding: GPC with digraphs, context-sensitive c/g/s,
    and silent final letters. This is the *ground truth* for regular words; for
    an irregular word it yields the (wrong) regularised reading."""
    w = word.lower()
    out: list[str] = []
    i, n = 0, len(w)
    while i < n:
        m = None
        for g, p in _DIGRAPHS:
            if w.startswith(g, i):
                if g in _NASAL_G:
                    nx = w[i + len(g):i + len(g) + 1]
                    if nx in _VOWELS or nx == g[-1]:
                        continue
                m = (g, p)
                break
        if m:
            out.append(m[1])
            i += len(m[0])
            continue
        c = w[i]
        nx = w[i + 1] if i + 1 < n else ""
        prev = w[i - 1] if i > 0 else ""
        last = i == n - 1
        if c == "c":
            out.append("s" if nx in _FRONT else "k")
        elif c == "g":
            out.append("Z" if nx in _GFRONT else "g")
        elif c == "s":
            out.append("" if (last and n > 2) else ("z" if (prev in _VOWELS and nx in _VOWELS) else "s"))
        elif c == "h":
            pass
        elif c == "x":
            out.append("" if last else "ks")
        elif c == "e":
            if not (last and n > 2):
                out.append("@")
        elif c in "td" and last and n > 2:
            pass   # silent final t/d
        else:
            out.append(_SIMPLE.get(c, c))
        i += 1
    out = [p for p in out if p]
    while out and out[-1] == "@":
        out.pop()
    return ".".join(out)


# Default phoneme → grapheme (for the dictée / encoding domain). A phonetic
# speller picks the commonest spelling and so drops silent letters and complex
# graphemes — the characteristic dictée error ("bateau" -> "bato").
_PHONEME_TO_GRAPHEME = {
    "a": "a", "e": "é", "E": "è", "i": "i", "o": "o", "y": "u", "U": "ou",
    "Z9": "eu", "@": "e", "AN": "an", "ON": "on", "IN": "in", "wa": "oi",
    "S": "ch", "Z": "j", "f": "f", "k": "c", "p": "p", "b": "b", "t": "t",
    "d": "d", "g": "g", "v": "v", "s": "s", "z": "z", "l": "l", "R": "r",
    "m": "m", "n": "n", "N": "gn", "ks": "x", "w": "w",
}


def phonetic_spelling(phonemes: str) -> str:
    """A naive phonetic spelling of a phoneme string (the dictée error)."""
    return "".join(_PHONEME_TO_GRAPHEME.get(p, p) for p in phonemes.split("."))


def decode_letterwise(word: str) -> str:
    """Absolute-beginner decoding: letter by letter, no digraphs, no silent
    finals. Correct only on the simplest words; on any word with a digraph or
    silent letter it diverges — the characteristic early-reader error."""
    w = word.lower()
    out: list[str] = []
    for ch in w:
        if ch == "c":
            out.append("k")
        elif ch == "h":
            continue
        elif ch == "e":
            out.append("@")
        else:
            out.append(_SIMPLE.get(ch, ch))
    return ".".join(out)


# ---- Word stocks -----------------------------------------------------------
# Regular words: decode_gpc gives the truth AND decode_letterwise gets it wrong
# (each has a digraph or a silent letter), so the GPC skill is genuinely needed.
REGULAR_WORDS = [
    "chat", "chou", "moulin", "bateau", "lapin", "fourmi", "manteau", "souris",
    "tapis", "chocolat", "pirate", "jardin", "mouton", "tortue", "banane",
    "robe", "tomate", "salade", "table", "fenêtre",
]
# Pseudo-words: decodable by rule, impossible to have memorised. The strongest
# transfer test for an alphabetic decoding skill.
PSEUDO_WORDS = ["molu", "tachi", "biron", "choma", "fluron", "rivon", "pabou", "lanche"]
# Real regular words held out of teaching entirely (rule transfer to new words).
TRANSFER_WORDS = ["domino", "chameau", "souricière", "ravioli", "bidon", "chalut"]

# Irregular / sight words: hand-specified truth; decode_gpc regularises wrongly.
IRREGULAR_WORDS = {
    "femme": "f.a.m", "monsieur": "m.@.s.j.Z9", "oignon": "o.N.ON",
    "sept": "s.E.t", "fils": "f.i.s", "pays": "p.E.i", "clef": "k.l.e",
    "second": "s.@.g.ON",
}

# Multi-syllable words with hand-verified syllable breaks (CP segmentation).
SYLLABLES = {
    "moulin": "mou-lin", "bateau": "ba-teau", "lapin": "la-pin",
    "fourmi": "four-mi", "manteau": "man-teau", "chocolat": "cho-co-lat",
    "pirate": "pi-rate", "jardin": "jar-din", "mouton": "mou-ton",
    "tortue": "tor-tue", "banane": "ba-nane", "salade": "sa-lade",
    "tomate": "to-mate", "domino": "do-mi-no",
}
SYLLABLES_TRANSFER = {"cinéma": "ci-né-ma", "tapis": "ta-pis", "vélo": "vé-lo",
                      "radis": "ra-dis", "képi": "ké-pi"}
# Words to write from dictation (encoding). Only words a phonetic speller gets
# WRONG (a silent letter or a non-default grapheme) — so the orthographic skill
# is genuinely required; transparent words (chou, lapin…) are excluded.
ENCODING_WORDS = [w for w in REGULAR_WORDS if phonetic_spelling(decode_gpc(w)) != w]
ENCODING_TRANSFER = ["chapeau", "gâteau", "cadeau", "rideau", "plateau"]

NODES_LECTURE: dict[str, dict] = {
    "fr.CP.lecture_mots_reguliers": {
        "title": "Lecture de mots réguliers (décodage)",
        "category": "reg",
        "required_skills": {"grapheme_phoneme": 0.5, "blending": 0.3, "grapheme_recognition": 0.2},
        "mastery_threshold": 0.8,
    },
    "fr.CP.lecture_mots_irreguliers": {
        "title": "Lecture de mots irréguliers (mots-outils)",
        "category": "irr",
        "required_skills": {"sight_words": 0.6, "grapheme_phoneme": 0.2, "grapheme_recognition": 0.2},
        "mastery_threshold": 0.8,
    },
    "fr.CP.comprehension_phrase": {
        "title": "Compréhension de phrase simple",
        "category": "comp",
        "required_skills": {"sentence_parsing": 0.4, "lexical_access": 0.4, "grapheme_phoneme": 0.2},
        "mastery_threshold": 0.8,
    },
    "fr.CP.segmentation_syllabes": {
        "title": "Segmentation en syllabes",
        "category": "syll",
        "required_skills": {"syllable_segmentation": 0.6, "blending": 0.2, "grapheme_recognition": 0.2},
        "mastery_threshold": 0.8,
    },
    "fr.CP.dictee_simple": {
        "title": "Dictée de mots simples (encodage)",
        "category": "enc",
        "required_skills": {"orthographic_encoding": 0.6, "grapheme_phoneme": 0.2, "grapheme_recognition": 0.2},
        "mastery_threshold": 0.8,
    },
}


@dataclass
class ReadingTask(Task):
    node_id: str
    word: str
    answer: str            # correct phoneme string
    required_skills: dict
    category: str          # "reg" | "irr"

    @property
    def prompt(self) -> str:
        return f"Lis le mot « {self.word} » (phonèmes) : ?"

    @property
    def working_set(self) -> list:
        return [self.word]

    def mistake(self, weak_skill: str) -> tuple[str, str]:
        if weak_skill == "sight_words":
            return decode_gpc(self.word), "overregularized_reading"   # femme -> /f@m/
        if weak_skill == "blending":
            first = self.answer.split(".")[0]
            return first, "no_blending"                              # only the first phoneme
        if weak_skill in ("grapheme_phoneme", "grapheme_recognition"):
            return decode_letterwise(self.word), "letter_by_letter"
        return "?", "no_decoding"


@dataclass
class SentenceTask(Task):
    node_id: str
    subject: str
    verb: str
    obj: str
    qtype: str             # "qui" -> answer subject ; "quoi" -> answer object
    answer: str
    required_skills: dict
    category: str = "comp"

    @property
    def prompt(self) -> str:
        q = "Qui ?" if self.qtype == "qui" else "Quoi ?"
        return f"« {self.subject} {self.verb} {self.obj} ». {q}"

    @property
    def working_set(self) -> list:
        return [self.subject, self.verb, self.obj, self.qtype]

    def mistake(self, weak_skill: str) -> tuple[str, str]:
        if weak_skill == "sentence_parsing":
            # role confusion: give the other argument
            return (self.obj if self.qtype == "qui" else self.subject), "role_confusion"
        if weak_skill == "lexical_access":
            return "?", "word_not_recognized"
        if weak_skill == "grapheme_phoneme":
            return "?", "cannot_decode"
        return "?", "no_comprehension"


@dataclass
class SyllableTask(Task):
    node_id: str
    word: str
    answer: str            # syllables joined by "-"
    required_skills: dict
    category: str = "syll"

    @property
    def prompt(self) -> str:
        return f"Découpe « {self.word} » en syllabes : ?"

    @property
    def working_set(self) -> list:
        return [self.word]

    def mistake(self, weak_skill: str) -> tuple[str, str]:
        if weak_skill in ("syllable_segmentation", "blending"):
            return self.word, "no_segmentation"          # leaves the word whole
        return self.word, "no_segmentation"


@dataclass
class EncodingTask(Task):
    node_id: str
    phonemes: str          # the "heard" word (prompt)
    answer: str            # correct written word
    required_skills: dict
    category: str = "enc"

    @property
    def prompt(self) -> str:
        return f"Écris le mot que tu entends [{self.phonemes}] : ?"

    @property
    def working_set(self) -> list:
        return [self.phonemes]

    def mistake(self, weak_skill: str) -> tuple[str, str]:
        if weak_skill in ("orthographic_encoding", "grapheme_phoneme", "grapheme_recognition"):
            return phonetic_spelling(self.phonemes), "phonetic_spelling"   # bateau -> bato
        return "?", "no_encoding"


# ---- Bank builders ---------------------------------------------------------
@dataclass
class Bank:
    teaching: list = None
    heldout: list = None

    def __post_init__(self):
        self.teaching = self.teaching or []
        self.heldout = self.heldout or []


def _reading_task(node_id: str, word: str, category: str) -> ReadingTask:
    spec = NODES_LECTURE[node_id]
    answer = IRREGULAR_WORDS[word] if category == "irr" else decode_gpc(word)
    return ReadingTask(node_id=node_id, word=word, answer=answer,
                       required_skills=dict(spec["required_skills"]), category=category)


def _syllable_task(node_id: str, word: str) -> SyllableTask:
    return SyllableTask(node_id, word, SYLLABLES.get(word) or SYLLABLES_TRANSFER[word],
                        dict(NODES_LECTURE[node_id]["required_skills"]))


def _encoding_task(node_id: str, word: str) -> EncodingTask:
    return EncodingTask(node_id, decode_gpc(word), word,
                        dict(NODES_LECTURE[node_id]["required_skills"]))


def build_bank_lecture(node_id: str, rng, frac_teach: float = 0.55) -> Bank:
    spec = NODES_LECTURE[node_id]
    cat = spec["category"]
    if cat == "comp":
        return _build_comprehension_bank(node_id, rng, frac_teach)
    if cat == "syll":
        words = list(SYLLABLES)
        make = _syllable_task
    elif cat == "enc":
        words = list(ENCODING_WORDS)
        make = lambda nid, w: _encoding_task(nid, w)  # noqa: E731
    else:
        words = list(REGULAR_WORDS) if cat == "reg" else list(IRREGULAR_WORDS)
        make = lambda nid, w: _reading_task(nid, w, cat)  # noqa: E731
    rng.shuffle(words)
    cut = max(1, int(len(words) * frac_teach))
    return Bank(teaching=[make(node_id, w) for w in words[:cut]],
                heldout=[make(node_id, w) for w in words[cut:]])


def transfer_bank_syllabes(node_id: str = "fr.CP.segmentation_syllabes") -> list:
    return [_syllable_task(node_id, w) for w in SYLLABLES_TRANSFER]


def transfer_bank_dictee(node_id: str = "fr.CP.dictee_simple") -> list:
    """Encoding transfer: write unseen words (with silent/complex graphemes)
    from their sounds."""
    return [_encoding_task(node_id, w) for w in ENCODING_TRANSFER]


def transfer_bank_lecture(node_id: str = "fr.CP.lecture_mots_reguliers") -> list:
    """Rule transfer for regular decoding: unseen real words + pseudo-words."""
    out = [_reading_task(node_id, w, "reg") for w in TRANSFER_WORDS]
    out += [_reading_task(node_id, w, "reg") for w in PSEUDO_WORDS]
    return out


# ---- Sentence comprehension ------------------------------------------------
_SUBJECTS = ["le chat", "la souris", "le lapin", "papa"]
_VERBS = ["mange", "regarde", "cherche"]
_OBJECTS = ["la pomme", "le livre", "la balle"]
_TRANSFER_VERB = "attrape"
_TRANSFER_OBJECT = "la fleur"


def _sentence_tasks(node_id: str, subj: str, verb: str, obj: str) -> list:
    spec = NODES_LECTURE[node_id]
    rs = dict(spec["required_skills"])
    return [
        SentenceTask(node_id, subj, verb, obj, "qui", subj, dict(rs)),
        SentenceTask(node_id, subj, verb, obj, "quoi", obj, dict(rs)),
    ]


def _build_comprehension_bank(node_id: str, rng, frac_teach: float) -> Bank:
    combos = [(s, v, o) for s in _SUBJECTS for v in _VERBS for o in _OBJECTS]
    rng.shuffle(combos)
    cut = max(1, int(len(combos) * frac_teach))
    teaching = [t for (s, v, o) in combos[:cut] for t in _sentence_tasks(node_id, s, v, o)]
    heldout = [t for (s, v, o) in combos[cut:] for t in _sentence_tasks(node_id, s, v, o)]
    return Bank(teaching=teaching, heldout=heldout)


def transfer_bank_comprehension(node_id: str = "fr.CP.comprehension_phrase") -> list:
    """Sentences built from known words but with a verb/object never used in
    teaching — comprehension generalises to new combinations."""
    out = []
    for s in _SUBJECTS:
        out += _sentence_tasks(node_id, s, _TRANSFER_VERB, _OBJECTS[0])
        out += _sentence_tasks(node_id, s, _VERBS[0], _TRANSFER_OBJECT)
    return out
