from typing import List
from app.models.experience import ExperienceModel
from app.experience.retain import retain_experience

SEED_EXPERIENCES = [
    ExperienceModel(
        experience_id="exp-incident-01",
        context="API v2 release with legacy auth middleware",
        service_name="payment-auth",
        agents_involved=["planner", "coder", "tester", "security"],
        decision="Stripped legacy authorization headers in API v2 migration patch",
        action="Deployed v2 endpoint omitting X-Legacy-Auth header support",
        validation="Integration tests failed with 401 Unauthorized for legacy web clients",
        outcome="FAILURE",
        root_cause="Legacy web & mobile app clients rely on legacy authorization header format",
        lesson="Always preserve X-Legacy-Auth header fallback when upgrading API v2 endpoints",
        future_applicability="API route migrations & auth middleware upgrades",
        tags=["legacy auth", "auth middleware", "api v2", "payment-auth"],
        source="seed"
    ),
    ExperienceModel(
        experience_id="exp-incident-02",
        context="Flaky async worker test suite race condition under load",
        service_name="async-worker",
        agents_involved=["planner", "coder", "tester", "security"],
        decision="Omitted connection timeout retry in worker queue listener",
        action="Applied patch without retry backoff handler",
        validation="Production outage during peak load spike: ConnectionPoolTimeout",
        outcome="FAILURE",
        root_cause="Missing exponential backoff retry in worker database pool",
        lesson="Enforce 300ms exponential retry policy on all async worker database connections",
        future_applicability="Async queue & event worker pool configurations",
        tags=["flaky test", "async worker", "race condition"],
        source="seed"
    ),
    ExperienceModel(
        experience_id="exp-incident-03",
        context="Kubernetes deployment missing DB_POOL_SIZE environment variable",
        service_name="user-service",
        agents_involved=["planner", "coder", "tester", "security"],
        decision="Updated deployment manifest without injecting database pool configuration secret",
        action="Pushed k8s manifest update",
        validation="Service pod crash loop: KeyError 'DB_POOL_SIZE'",
        outcome="FAILURE",
        root_cause="Environment variable DB_POOL_SIZE not present in staging ConfigMap",
        lesson="Inject fallback default value (DB_POOL_SIZE=10) directly in container initialization script",
        future_applicability="Kubernetes manifest environment secret injections",
        tags=["env variable", "misconfig", "k8s"],
        source="seed"
    ),
    ExperienceModel(
        experience_id="exp-incident-04",
        context="Staging DB migration index lock deadlock timeout",
        service_name="order-service",
        agents_involved=["planner", "coder", "tester"],
        decision="Ran synchronous CREATE INDEX on 50M row orders table during active traffic",
        action="Executed unthrottled schema migration",
        validation="Exclusive table lock caused 504 Gateway Timeout across order placement",
        outcome="FAILURE",
        root_cause="Synchronous index creation acquires ACCESS EXCLUSIVE lock on PostgreSQL table",
        lesson="Always execute large table index builds using CREATE INDEX CONCURRENTLY",
        future_applicability="Database schema migrations on high volume tables",
        tags=["db migration", "index lock", "postgres"],
        source="seed"
    ),
    ExperienceModel(
        experience_id="exp-incident-05",
        context="OAuth refresh token secret rotation misconfiguration",
        service_name="auth-service",
        agents_involved=["planner", "coder", "security"],
        decision="Rotated signing key secret without retaining previous key for grace period",
        action="Updated JWT secret key instantly in auth server",
        validation="Invalidated all active user session tokens simultaneously",
        outcome="FAILURE",
        root_cause="Immediate secret key invalidation breaks active refresh tokens",
        lesson="Maintain dual active signing key rotation window for 48 hours during secret rotation",
        future_applicability="OAuth secret rotation & JWT signing key updates",
        tags=["oauth", "jwt", "secret rotation"],
        source="seed"
    ),
    ExperienceModel(
        experience_id="exp-incident-06",
        context="Kafka event consumer deserialization schema mismatch outage",
        service_name="notification-service",
        agents_involved=["planner", "coder", "tester"],
        decision="Added non-optional timestamp field to Kafka event payload without schema registry update",
        action="Published v2 event format to kafka topic",
        validation="Notification consumers threw NullPointerException on legacy event parsing",
        outcome="FAILURE",
        root_cause="Consumers lacked defensive optional field parsing for unversioned topic messages",
        lesson="Define schema compatibility mode to FULL_TRANSITIONAL before altering Kafka event payloads",
        future_applicability="Event-driven streaming schema migrations",
        tags=["kafka", "event stream", "schema mismatch"],
        source="seed"
    )
]

def seed_hindsight_experiences() -> int:
    """
    Seeds Hindsight experience memory vault with realistic synthetic incident memories.
    """
    count = 0
    for exp in SEED_EXPERIENCES:
        retain_experience(exp)
        count += 1
    print(f"[Hindsight Seed] Successfully seeded {count} incident memories into Hindsight vault.")
    return count
