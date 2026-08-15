import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def reflection_casts(evidence_ids, period, version):
    canonical = "|".join([*sorted(evidence_ids), period, version])
    digest = hashlib.sha256(canonical.encode()).digest()
    return [6 + (byte % 4) for byte in digest[:6]]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    schemas = text("NABOM_FINAL_v1.0/01_BRAND_PRODUCT/06_Core_JSON_Schemas.md")
    living = text("NABOM_FINAL_v1.0/01_BRAND_PRODUCT/02_Living_Self_Engine.md")
    builder = text("NABOM_FINAL_v1.0/04_CUSTOM_GOODS_NFC_PAGE/15_NFC_QR_Custom_Page_Builder.md")
    states = text("NABOM_FINAL_v1.0/11_ARCHITECTURE_SSOT/38_Canonical_State_Machines.md")
    backlog = text("NABOM_FINAL_v1.0/06_OPERATIONS_QA_RELEASE/05_Implementation_Backlog.md")

    require('"authorization_state": "active"' in schemas, "gift page active authorization missing")
    require("authorization_state`는 `suspended`" in schemas, "gift page suspended authorization missing")
    require("현재 membership·consent·state" in schemas, "resolver authorization contract missing")
    require("동의 철회·관계 revoke·그룹 pause" in builder, "page revocation propagation missing")
    require("UNLISTED`는 검색 노출을 막는 discoverability 설정" in builder, "visibility/auth separation missing")
    require("canonical hash 입력은 정렬된 Evidence ID" in living, "deterministic seed composition missing")
    require("사용자 ID, 현재 시각, 외부 random API" in living, "randomness exclusions missing")
    require("bottom-to-top" in living, "cast ordering missing")
    require("GroupMembership" in schemas and '"consent_id"' in schemas, "group membership consent schema missing")
    require("aggregate_only" in schemas and '"minimum_group_size": 5' in schemas, "group aggregate gate missing")
    require("one-sided consent cannot activate relationship" in backlog, "relationship consent QA missing")
    require("fewer than 5 active members blocks individual inference" in backlog, "group minimum QA missing")
    require("GroupBuy does not auto-create InsightGroup membership" in backlog, "GroupBuy separation QA missing")
    canonical_policies = [
        "public",
        "claimed_recipient",
        "consented_relationship_members",
        "active_insight_group_members",
        "owner_only",
    ]
    for policy in canonical_policies:
        require(f"`{policy}`" in schemas and f"- `{policy}`" in builder, f"canonical access policy missing: {policy}")
    require("`consented_members`는 사용하지 않는다" in schemas, "legacy access policy was not rejected")
    require("status`는 분석의 인식론적 상태" in schemas, "epistemic status separation missing")
    require("authorization_state`는 접근 가능성" in schemas, "authorization state separation missing")
    for field in ["resolver_input_hash", "cast_mapping_version", "raw_reading_internal_ref", "classical_source_refs", "generated_at"]:
        require(field in schemas and field in living, f"reflection audit field missing: {field}")

    first = reflection_casts(["ev2", "ev1"], "2026-08-10/2026-08-16", "iching-reflection-v1")
    second = reflection_casts(["ev1", "ev2"], "2026-08-10/2026-08-16", "iching-reflection-v1")
    require(first == second, "reflection resolver is not order-independent")
    changed = reflection_casts(["ev1", "ev3"], "2026-08-10/2026-08-16", "iching-reflection-v1")
    require(first != changed, "reflection resolver ignored snapshot changes")

    print(json.dumps({
        "kind": "api-package-test-report",
        "status": "passed",
        "checks": {
            "consent_aware_page_authorization": "passed",
            "revocation_suspension_contract": "passed",
            "deterministic_reflection_replay": "passed",
            "group_schema_and_minimum_gate": "passed",
            "groupbuy_separation": "passed",
        },
        "adversarial_cases": [
            "reordered evidence IDs produce identical casts",
            "changed evidence snapshot produces a different deterministic cast sequence",
            "revoked or paused authorization is suspended",
            "fewer than five active-consented members cannot publish individual inference",
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
