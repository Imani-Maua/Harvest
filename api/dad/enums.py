from enum import Enum


class EvidenceSource(str, Enum):
    manual = "manual"        # user typed it
    cv = "cv"                # extracted from CV upload
    ai_inferred = "ai_inferred"  # AI filled in a gap
    linkedin = "linkedin"    # imported from LinkedIn (future)


class WorkAuthorisation(str, Enum):
    requires_sponsorship = "requires_sponsorship"


class RemotePreference(str, Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    flexible = "flexible"


class SkillCategory(str, Enum):
    language = "language"
    framework = "framework"
    tool = "tool"
    platform = "platform"
    soft = "soft"
    domain = "domain"
    other = "other"


class SkillProficiency(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class LinkType(str, Enum):
    portfolio = "portfolio"
    github = "github"
    linkedin = "linkedin"
    blog = "blog"
    publication = "publication"
    other = "other"


class JobStatus(str, Enum):
    watch_list = "watch_list"
    applied = "applied"
    in_pipeline = "in_pipeline"
    rejected = "rejected"
    offered = "offered"


class SponsorshipStatus(str, Enum):
    confirmed = "confirmed"
    explicitly_unavailable = "explicitly_unavailable"
    possible = "possible"
    no_info = "no_info"
    requires_clarification = "requires_clarification"
