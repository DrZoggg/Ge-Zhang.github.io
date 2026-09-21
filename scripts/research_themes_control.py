import argparse
import copy
import os
import sys

from build_publications import build_site
from site_common import (
    PROFILE_CONFIG_PATH,
    load_profile_config,
    validate_homepage_research,
    write_json,
)
from validate_site import validate_site


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


def normalized_optional(value):
    return str(value or "").strip()


def protected_profile(profile):
    return {
        key: copy.deepcopy(value)
        for key, value in profile.items()
        if key != "homepage_research"
    }


def apply_updates(profile, args):
    updated = copy.deepcopy(profile)
    section = updated["homepage_research"]
    changed_fields = []

    for input_name, config_key in (
        ("section_label", "label"),
        ("section_heading", "heading"),
    ):
        value = normalized_optional(getattr(args, input_name))
        if value and section[config_key] != value:
            section[config_key] = value
            changed_fields.append(input_name)

    for position in range(1, 5):
        action = getattr(args, f"theme_{position}_action")
        title = normalized_optional(getattr(args, f"theme_{position}_title"))
        description = normalized_optional(
            getattr(args, f"theme_{position}_description")
        )
        if position > len(section["themes"]):
            if action != "no_change" or title or description:
                raise ValueError(
                    f"Homepage research theme {position} does not exist in the profile."
                )
            continue

        theme = section["themes"][position - 1]
        if action != "no_change":
            enabled = action == "enable"
            if theme["enabled"] != enabled:
                theme["enabled"] = enabled
                changed_fields.append(f"theme_{position}_enabled")

        for field, value in (("title", title), ("description", description)):
            if value and theme[field] != value:
                theme[field] = value
                changed_fields.append(f"theme_{position}_{field}")

    validate_homepage_research(updated)
    return updated, changed_fields


def render_summary(changed_fields):
    field_lines = [f"- {field}" for field in changed_fields] or ["- none"]
    return "\n".join(
        [
            "# Research Themes Control Center",
            "",
            "Updated fields:",
            *field_lines,
            "",
            "Protected profile and publication fields:",
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
    protected_before = protected_profile(original)
    updated, changed_fields = apply_updates(original, args)
    if protected_profile(updated) != protected_before:
        raise ValueError(
            "Research Themes Control Center attempted to change a protected profile field."
        )

    profile_changed = updated != original
    if profile_changed:
        write_json(PROFILE_CONFIG_PATH, updated)

    build_result = build_site()
    validation = validate_site()
    if protected_profile(load_profile_config()) != protected_before:
        raise ValueError(
            "A protected profile field changed during the research themes operation."
        )

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
        description="Update the human-visible homepage research themes."
    )
    result.add_argument(
        "--section-label", default=os.environ.get("SECTION_LABEL_INPUT", "")
    )
    result.add_argument(
        "--section-heading", default=os.environ.get("SECTION_HEADING_INPUT", "")
    )
    for position in range(1, 5):
        result.add_argument(
            f"--theme-{position}-action",
            choices=("no_change", "enable", "disable"),
            default=os.environ.get(
                f"THEME_{position}_ACTION_INPUT", "no_change"
            ),
        )
        result.add_argument(
            f"--theme-{position}-title",
            default=os.environ.get(f"THEME_{position}_TITLE_INPUT", ""),
        )
        result.add_argument(
            f"--theme-{position}-description",
            default=os.environ.get(f"THEME_{position}_DESCRIPTION_INPUT", ""),
        )
    return result


def main():
    args = parser().parse_args()
    try:
        run_control(args)
    except Exception as exc:
        message = f"# Research Themes Control Center\n\n**FAILED:** {exc}"
        output_value("profile_changed", "false")
        append_summary(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
