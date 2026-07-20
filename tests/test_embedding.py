from humanvals.embedding import HashedNgramEmbedder, cosine
from humanvals.retrieval import SIMILARITY_GATE


def test_identical_texts_similarity_one() -> None:
    e = HashedNgramEmbedder()
    v = e.embed('refund my order please')
    assert abs(cosine(v, v) - 1.0) < 1e-9


def test_related_beats_unrelated() -> None:
    e = HashedNgramEmbedder()
    base = e.embed('I want a refund for my order')
    related = e.embed('can I get a refund for this order?')
    unrelated = e.embed('what is the weather in Berlin')
    assert cosine(base, related) > cosine(base, unrelated)
    assert cosine(base, related) > SIMILARITY_GATE
    assert cosine(base, unrelated) < SIMILARITY_GATE


def test_stopwords_do_not_carry_similarity() -> None:
    e = HashedNgramEmbedder()
    a = e.embed('please can I get it for my order')
    b = e.embed('would you like to do that with the meeting')
    assert cosine(a, b) < 0.2  # only function words shared -> near zero


def test_varied_phrasings_clear_the_gate() -> None:
    """Calibration guard for the default embedder + gate (ADR-0004)."""
    e = HashedNgramEmbedder()
    intent = e.embed('Requesting a refund for order #7742, packaging was damaged '
                     'refund requests')
    related = [
        'Please refund my order #2210, it arrived scratched',
        'Can I get a refund on my order #9134? It arrived defective',
        'Refund my order #7008, the item arrived dead on arrival',
    ]
    unrelated = ['what is the weather in Berlin', 'how do I change my password',
                 'schedule a meeting with the sales team', 'cancel my subscription plan']
    for q in related:
        assert cosine(intent, e.embed(q)) >= SIMILARITY_GATE, q
    for q in unrelated:
        assert cosine(intent, e.embed(q)) < SIMILARITY_GATE - 0.1, q


def test_deterministic_across_instances() -> None:
    assert HashedNgramEmbedder().embed('hello world') == HashedNgramEmbedder().embed('hello world')


def test_empty_text_is_zero_vector() -> None:
    v = HashedNgramEmbedder().embed('')
    assert cosine(v, v) == 0.0
