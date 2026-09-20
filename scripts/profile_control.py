import argparse
import copy
import os
import re
import sys

from build_publications import build_site
from site_common import PROFILE_CONFIG_PATH, load_profile_config, write_json
from validate_site import validate_site


PROTECTED_IDENTITY_FIELDS = (
    "researcher_name",
    "researcher_name_zh",
    "given_name",
    "family_name",
    "person_id",
    "orcid",
    "external_links",
)


def append_summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(text.rstrip() + "\n")


def output_value(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def protected_identity(profile):
    return {
        field: copy.deepcopy(profile.get(field))
        for field in PROTECTED_IDENTITY_FIELDS
    }


def normalized_optional(value):
    return str(value or "").strip()


def parse_research_areas(raw):
    value = normalized_optional(raw)
    if not value:
        return None
    areas = []
    seen = set()
    for item in re.split(r"[,\r\n]+", value):
        area = item.strip()
        if not area:
            continue
        key = area.casefold()
        if key not in seen:
            seen.add(key)
            areas.append(area)
    if not areas:
        raise ValueError(
            "research_areas must contain at least one non-empty comma- or newline-separated item."
        )
    return areas


def apply_updates(profile, args):
    updated = copy.deepcopy(profile)
    changed_fields = []

    scalar_fields = (
        ("biography_en", ("biography", "en")),
        ("biography_zh", ("biography", "zh")),
        ("description", ("description",)),
        (
            "disambiguating_description",
            ("disambiguating_description",),
        ),
    )
    for input_name, path in scalar_fields:
        value = normalized_optional(getattr(args, input_name))
        if not value:
            continue
        target = updated
        for key in path[:-1]:
            target = target[key]
        if target[path[-1]] != value:
            target[path[-1]] = value
            changed_fields.append(input_name)

    affiliation = normalized_optional(args.primary_affiliation)
    if affiliation and updated["affiliations"][0]["name"] != affiliation:
        updated["affiliations"][0]["name"] = affiliation
        changed_fields.append("primary_affiliation")

    research_areas = parse_research_areas(args.research_areas)
    if research_areas is not None and updated["research_areas"] != research_areas:
        updated["research_areas"] = research_areas
        changed_fields.append("research_areas")

    return updated, changed_fields


def render_summary(changed_fields):
    field_lines = [f"- {field}" for field in changed_fields] or ["- none"]
    return "\n".join(
        [
            "# Profile Control Center",
            "",
            "Updated fields:",
            *field_lines,
            "",
            "Protected identity fields:",
            "UNCHANGED",
            "",
            "Build:",
            "PASS",
            "",
            "Validator:",
            "PASS",
        ]
    )


def run_control(args):
    original = load_profile_config()
    identity_before = protected_identity(original)
    updated, changed_fields = apply_updates(original, args)
    if protected_identity(updated) != identity_before:
        raise ValueError("Profile Control Center attempted to change a protected identity field.")

    profile_changed = updated != original
    if profile_changed:
        write_json(PROFILE_CONFIG_PATH, updated)

    build_result = build_site()
    validation = validate_site()
    identity_after = protected_identity(load_profile_config())
    if identity_after != identity_before:
        raise ValueError("A protected identity field changed during the profile control operation.")

    output_value("profile_changed", str(profile_changed).lower())
    output_value("updated_fields", ",".join(changed_fields))
    report = render_summary(changed_fields)
    append_summary(report)
    print(report)
    return {
        "profile_changed": profile_changed,
        "updated_fields": changed_fields,
        "build": build_result,
        "validation": validation,
    }


def parser():
    result = argparse.ArgumentParser(
        description="Update presentation fields in data/profile_config.json."
    )
    result.add_argument(
        "--biography-en", default=os.environ.get("BIOGRAPHY_EN_INPUT", "")
    )
    result.add_argument(
        "--biography-zh", default=os.environ.get("BIOGRAPHY_ZH_INPUT", "")
    )
    result.add_argument(
        "--primary-affiliation",
        default=os.environ.get("PRIMARY_AFFILIATION_INPUT", ""),
    )
    result.add_argument(
        "--research-areas", default=os.environ.get("RESEARCH_AREAS_INPUT", "")
    )
    result.add_argument(
        "--description", default=os.environ.get("DESCRIPTION_INPUT", "")
    )
    result.add_argument(
        "--disambiguating-description",
        default=os.environ.get("DISAMBIGUATING_DESCRIPTION_INPUT", ""),
    )
    return result


def main():
    args = parser().parse_args()
    try:
        run_control(args)
    except Exception as exc:
        message = f"# Profile Control Center\n\n**FAILED:** {exc}"
        output_value("profile_changed", "false")
        append_summary(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
