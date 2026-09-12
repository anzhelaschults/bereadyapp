from beready.trails import TRAILS


def test_every_trail_has_three_level_specific_challenge_sets():
    for trail in TRAILS.values():
        content = trail['content']
        assert set(content['challenges']) == {'1','2','3'}
        for level in ('1','2','3'):
            assert len(content['challenges'][level]) >= 2
            for challenge in content['challenges'][level]:
                assert set(challenge) == {'title','icon','text'}
                assert all(challenge.values())
        assert content['challenges']['1'] != content['challenges']['3']
        assert content['worth_it']
        assert content['review_status'] == 'review pending'


def test_sources_are_links_not_provenance_prose():
    for trail in TRAILS.values():
        assert all(source.startswith('https://') for source in trail['sources'])


def test_curated_copy_has_no_forbidden_punctuation():
    for trail in TRAILS.values():
        copy = str(trail['content']) + trail['season_note']
        assert '—' not in copy and ';' not in copy
