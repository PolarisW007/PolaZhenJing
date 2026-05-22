from app.owner_identity import is_owner_alias, resolve_actor


class FakeDb:
    def __init__(self, row):
        self.row = row

    def execute(self, *_args, **_kwargs):
        return self

    def fetchone(self):
        return self.row


def test_owner_aliases_include_required_accounts():
    assert is_owner_alias(email="wsyxjer@gmail.com")
    assert is_owner_alias(email="wsyxjer@qq.com")
    assert is_owner_alias(username="18667107187")


def test_resolve_actor_marks_owner_by_email():
    actor = resolve_actor(
        {"user_id": 7},
        db_getter=lambda: FakeDb({
            "id": 7,
            "username": "Polaris",
            "email": "wsyxjer@qq.com",
            "role": "user",
        }),
    )

    assert actor.is_owner
    assert actor.subject_id == "owner"
    assert actor.trust_tier == "owner"


def test_resolve_actor_keeps_visitor_anonymous():
    actor = resolve_actor({})

    assert not actor.is_authenticated
    assert actor.identity_scope == "visitor"
    assert actor.subject_id == "visitor:anonymous"
