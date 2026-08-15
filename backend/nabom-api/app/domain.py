"""NABOM relationship / insight-group domain logic (pure, store-agnostic).

Implements the canonical contracts from NABOM_관계그룹_동의도메인_계약_v1.1:
- Relationship consent state machine (DRAFT→CONSENT_PENDING→ACTIVE→PAUSED→REVOKED)
- public trait scope enforcement
- directional RelationshipMirror (A→B / B→A / shared)
- immutable RelationshipEvidence (append-only)
- InsightGroup minimum-five aggregate gate + anonymized GroupProfile
- GroupBuy/InsightGroup namespace separation
- group-to-group aggregate-only insight
"""

from __future__ import annotations

import uuid

MINIMUM_GROUP_SIZE = 5

RELATIONSHIP_STATES = {"draft", "consent_pending", "active", "paused", "revoked", "deleted"}
CONSENT_SCOPES = {"birth_hypothesis", "character_profile", "trait_state", "relationship_mirror", "relationship_evidence"}
DEFAULT_SCOPE = {"birth_hypothesis", "character_profile", "relationship_mirror"}

GROUP_STATES = {"draft", "inviting", "active", "paused", "archived"}
MEMBER_STATES = {"invited", "joined", "active", "left", "removed"}

# 엔진 feature rule_code → 방향성 매핑 (RelationshipMirror 분해용)
A_TO_B_RULES = {"element_balance_reciprocal", "secondary_use_element_complement"}
B_TO_A_RULES = {"element_balance_complement", "useful_element_complement"}
SHARED_RULES = {
    "stem_same_element", "stem_generates_partner", "stem_supported_by_partner",
    "stem_combine", "branch_six_harmony", "branch_triad", "branch_seasonal",
    "ten_god_role_fit", "twelve_shinsal_resonance",
}
TENSION_RULES = {"stem_clash", "stem_controls_partner", "stem_controlled_by_partner", "branch_clash", "branch_punishment"}

# scope → 허용 feature 코드
SCOPE_FEATURES = {
    "birth_hypothesis": {
        "day_stem_relation", "day_branch_relation", "element_balance_complement",
        "ten_god_role_fit", "useful_element_support", "relationship_trigger_risk",
        "twelve_shinsal_resonance", "data_quality_confidence",
    },
    "character_profile": {"ten_god_role_fit", "twelve_shinsal_resonance"},
    "trait_state": set(),
    "relationship_mirror": {
        "day_stem_relation", "day_branch_relation", "element_balance_complement",
        "ten_god_role_fit", "useful_element_support", "relationship_trigger_risk",
        "twelve_shinsal_resonance", "data_quality_confidence",
    },
}


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Relationship ────────────────────────────────────────────────────────────

class Relationship:
    def __init__(self, relationship_id: str, initiator: str, participant: str, context: str):
        if initiator == participant:
            raise ValueError("self_relationship_not_allowed")
        self.id = relationship_id
        self.initiator = initiator
        self.participant = participant
        self.context = context
        self.state = "draft"
        self.consents: dict[str, set[str]] = {initiator: set(), participant: set()}
        self.evidence: list[dict] = []
        self._birth_inputs: dict[str, dict] = {}
        self.created_at = "2026-08-12T00:00:00Z"

    def set_birth_input(self, user_id: str, birth_input: dict):
        if user_id not in self.consents:
            raise ValueError("not_a_participant")
        self._birth_inputs[user_id] = birth_input

    def participants(self):
        return (self.initiator, self.participant)

    def grant_consent(self, user_id: str, scopes: list[str]):
        if user_id not in self.consents:
            raise ValueError("not_a_participant")
        if self.state == "revoked":
            raise ValueError("relationship_revoked")
        if (
            not isinstance(scopes, (list, set, frozenset))
            or not all(isinstance(scope, str) for scope in scopes)
            or not set(scopes) <= CONSENT_SCOPES
        ):
            raise ValueError("invalid_consent_scope")
        self.consents[user_id] = set(scopes) & CONSENT_SCOPES
        if self.state == "draft":
            self.state = "consent_pending"
        if self.consents[self.initiator] and self.consents[self.participant]:
            self.state = "active"
        elif self.state == "active":
            self.state = "paused"

    def revoke_consent(self, user_id: str):
        if user_id not in self.consents:
            raise ValueError("not_a_participant")
        self.consents[user_id] = set()
        if self.state in {"active", "consent_pending"}:
            self.state = "paused"

    def revoke(self):
        self.state = "revoked"

    def add_evidence(self, author: str, content: str, observations: list[str], consent_scope: str):
        if author not in self.consents:
            raise ValueError("not_a_participant")
        if self.state != "active":
            raise ValueError("relationship_not_active")
        if consent_scope != "relationship_evidence":
            raise ValueError("invalid_consent_scope")
        if any("relationship_evidence" not in self.active_scope(user_id) for user_id in self.participants()):
            raise ValueError("relationship_evidence_consent_required")
        event = {
            "evidence_id": new_id("rev"),
            "relationship_id": self.id,
            "source": "shared_checkin",
            "author_user_id": author,
            "content_ref": new_id("shared_entry"),
            "observations": observations,
            "consent_scope": consent_scope,
            "created_at": "2026-08-12T00:00:00Z",
        }
        self.evidence.append(event)  # append-only: 수정/삭제 없음
        return event

    def list_evidence(self, requester: str) -> list[dict]:
        if requester not in self.consents:
            raise ValueError("not_a_participant")
        if self.state != "active":
            raise ValueError("relationship_not_active")
        if any("relationship_evidence" not in self.active_scope(user_id) for user_id in self.participants()):
            raise ValueError("relationship_evidence_consent_required")
        return list(self.evidence)

    def active_scope(self, user_id: str) -> set[str]:
        return set(self.consents.get(user_id, set()))

    def to_dict(self):
        return {
            "relationship_id": self.id,
            "initiator_user_id": self.initiator,
            "participant_user_id": self.participant,
            "context": self.context,
            "status": self.state,
            "visibility": "private",
            "consents": {u: sorted(s) for u, s in self.consents.items()},
            "evidence_count": len(self.evidence),
        }

    def to_store(self) -> dict:
        return {
            "relationship_id": self.id,
            "initiator_user_id": self.initiator,
            "participant_user_id": self.participant,
            "context": self.context,
            "state": self.state,
            "consents": {u: sorted(s) for u, s in self.consents.items()},
            "evidence": self.evidence,
            "birth_inputs": self._birth_inputs,
        }

    @classmethod
    def from_store(cls, data: dict) -> "Relationship":
        rel = cls(data["relationship_id"], data["initiator_user_id"], data["participant_user_id"], data["context"])
        rel.state = data["state"]
        rel.consents = {u: set(s) for u, s in data.get("consents", {}).items()}
        rel.evidence = list(data.get("evidence", []))
        rel._birth_inputs = dict(data.get("birth_inputs", {}))
        return rel


def decompose_mirror(feature_scores: list[dict], allowed_features: set[str]) -> dict:
    """feature_scores → A→B / B→A / shared / tensions. 허용 feature만 사용."""
    if not isinstance(feature_scores, list):
        raise ValueError("invalid_feature_scores")
    a_to_b: list[str] = []
    b_to_a: list[str] = []
    shared: list[str] = []
    tensions: list[str] = []
    for feature in feature_scores:
        if (
            not isinstance(feature, dict)
            or not isinstance(feature.get("feature_code"), str)
            or not isinstance(feature.get("ko_name"), str)
        ):
            raise ValueError("invalid_feature_scores")
        notes = feature.get("notes", [])
        if not isinstance(notes, list):
            raise ValueError("invalid_feature_scores")
        for note in notes:
            if not isinstance(note, dict):
                raise ValueError("invalid_feature_scores")
        if feature["feature_code"] not in allowed_features:
            continue
        for note in notes:
            rule = note.get("rule_code", "")
            good = note.get("good", "")
            caution = note.get("caution", "")
            if rule in TENSION_RULES or note.get("bucket") in {"caution", "tension"}:
                if caution:
                    tensions.append(f"[{feature['ko_name']}] {caution}")
            elif rule in A_TO_B_RULES and good:
                a_to_b.append(f"[{feature['ko_name']}] {good}")
            elif rule in B_TO_A_RULES and good:
                b_to_a.append(f"[{feature['ko_name']}] {good}")
            elif rule in SHARED_RULES and good:
                shared.append(f"[{feature['ko_name']}] {good}")
            elif good and note.get("bucket") in {"good", "support"}:
                shared.append(f"[{feature['ko_name']}] {good}")
    return {
        "a_to_b": a_to_b[:5],
        "b_to_a": b_to_a[:5],
        "shared": shared[:5],
        "tensions": tensions[:5],
    }


# ── InsightGroup ────────────────────────────────────────────────────────────

class InsightGroup:
    def __init__(self, group_id: str, owner: str, name: str):
        self.id = group_id
        self.owner = owner
        self.name = name
        self.state = "inviting"
        self.members: dict[str, dict] = {}
        self.created_at = "2026-08-12T00:00:00Z"

    def add_owner(self):
        """Create the owner's already-authorized membership during group creation."""
        if self.owner in self.members:
            raise ValueError("already_member")
        self.members[self.owner] = {
            "role": "owner",
            "status": "active",
            "visibility_scope": "character_only",
            "consent_granted": True,
            "consent_status": "granted",
            "joined_at": "2026-08-12T00:00:00Z",
        }
        self._sync_state()

    def add_member(self, user_id: str, role: str = "member", visibility_scope: str = "character_only"):
        if user_id in self.members:
            raise ValueError("already_member")
        self.members[user_id] = {
            "role": role,
            "status": "invited",
            "visibility_scope": visibility_scope,
            "consent_granted": False,
            "consent_status": "requested",
            "invited_at": "2026-08-12T00:00:00Z",
            "joined_at": None,
        }
        self._sync_state()

    def grant_member_consent(self, user_id: str):
        member = self.members.get(user_id)
        if member is None:
            raise ValueError("not_a_member")
        if member.get("status") in {"left", "removed"}:
            raise ValueError("member_not_active")
        member["status"] = "active"
        member["consent_granted"] = True
        member["consent_status"] = "granted"
        member.setdefault("invited_at", "2026-08-12T00:00:00Z")
        member["joined_at"] = member.get("joined_at") or "2026-08-12T00:00:00Z"
        self._sync_state()

    def decline_member_consent(self, user_id: str):
        member = self.members.get(user_id)
        if member is None:
            raise ValueError("not_a_member")
        if member.get("status") in {"left", "removed"}:
            raise ValueError("member_not_active")
        member["consent_granted"] = False
        member["consent_status"] = "declined"
        self._sync_state()

    def _sync_state(self):
        if self.active_member_count() >= MINIMUM_GROUP_SIZE:
            self.state = "active"
        elif self.state == "active":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "paused"
        else:
            self.state = "inviting"

    def to_store(self) -> dict:
        return {"group_id": self.id, "owner": self.owner, "name": self.name, "state": self.state, "members": self.members}


    @classmethod
    def from_store(cls, data: dict) -> "InsightGroup":
        group = cls(data["group_id"], data["owner"], data["name"])
        group.state = data["state"]
        group.members = dict(data.get("members", {}))
        return group

    def active_member_count(self) -> int:
        return sum(1 for m in self.members.values() if m.get("status") == "active" and m.get("consent_granted") is True)

    def aggregate_profile(self, member_profiles: list[dict]) -> dict:
        """익명 집계: 개인 단위 기여를 노출하지 않는다. 최소 5명 미만은 추론 금지."""
        count = self.active_member_count()
        profiled = len(member_profiles)
        if count < MINIMUM_GROUP_SIZE or profiled < MINIMUM_GROUP_SIZE:
            return {
                "group_profile_id": new_id("gp"),
                "group_id": self.id,
                "status": "insufficient_members",
                "aggregate_only": False,
                "active_consented_member_count": count,
                "profiled_member_count": profiled,
                "minimum_group_size": MINIMUM_GROUP_SIZE,
                "shared_goals": [],
                "message": "최소 5명의 활성 동의 구성원(프로필 포함)이 필요합니다.",
            }
        elements = ["wood", "fire", "earth", "metal", "water"]
        totals = {e: 0.0 for e in elements}
        for profile in member_profiles:
            ratios = profile.get("ratio", {})
            for e in elements:
                totals[e] += ratios.get(e, 0.0)
        mean = {e: round(totals[e] / profiled, 4) for e in elements}
        dominant = max(elements, key=lambda e: mean[e])
        deficient = min(elements, key=lambda e: mean[e])
        return {
            "group_profile_id": new_id("gp"),
            "group_id": self.id,
            "status": "active",
            "aggregate_only": True,
            "anonymization": "k_anonymous",
            "active_consented_member_count": count,
            "profiled_member_count": profiled,
            "minimum_group_size": MINIMUM_GROUP_SIZE,
            "mean_element_ratio": mean,
            "group_dominant_element": dominant,
            "group_deficient_element": deficient,
            "shared_goals": [],
            "evidence_refs": [],
        }


def group_to_group_insight(group_a: dict, group_b: dict) -> dict:
    """그룹 간 분석: aggregate-only. 개인 역산 불가."""
    if not group_a.get("aggregate_only") or not group_b.get("aggregate_only"):
        raise ValueError("group_insight_requires_aggregate_only")
    a_dom, b_dom = group_a["group_dominant_element"], group_b["group_dominant_element"]
    a_def = group_a["group_deficient_element"]
    b_def = group_b["group_deficient_element"]
    return {
        "group_relationship_insight_id": new_id("gri"),
        "group_a_id": group_a["group_id"],
        "group_b_id": group_b["group_id"],
        "group_a_contributes": [{"element": a_dom, "note": f"{a_dom} 기반 추진·활성 에너지를 제공할 가능성"}],
        "group_b_contributes": [{"element": b_dom, "note": f"{b_dom} 기반 추진·활성 에너지를 제공할 가능성"}],
        "shared_improvement": [
            {"element": a_def, "note": f"그룹A의 {a_def} 영역을 공동 보완하면 좋을 가능성"},
            {"element": b_def, "note": f"그룹B의 {b_def} 영역을 공동 보완하면 좋을 가능성"},
        ],
        "coordination_risks": [],
        "recommended_joint_experiment": {"title": "공동 목표의 담당 경계를 먼저 합의", "success_condition": "다음 협업 1회에서 역할·완료 조건 기록"},
        "confidence": "low",
        "aggregate_only": True,
        "evidence_refs": [],
    }
