# AGENTS.md

Guidance for automated coding agents working in the SELinux Reference Policy repository.

## Authority and Documentation

For Reference Policy behavior, this repository and its documentation are authoritative. For
general SELinux concepts, behavior, policy languages, object classes, permissions, tools, and
configuration, use the
[SELinux Notebook](https://github.com/SELinuxProject/selinux-notebook/tree/main/src). If neither
source answers the question, consult the upstream SELinux userspace manual pages under
`https://github.com/SELinuxProject/selinux/*/man/**`.

Consult these repository documents when relevant:

| Task                                                   | Authority                      |
|--------------------------------------------------------|--------------------------------|
| Project overview and goals                             | `README.md`                    |
| Repository paths and generated files                   | `doc/REPO_LAYOUT.md`           |
| Design concepts and historical context                 | `doc/WHITEPAPER.md`            |
| Terminology and definitions                            | `doc/GLOSSARY.md`              |
| Security-effect evaluation                             | `doc/SECURITY_GOALS.md`        |
| Type-enforcement and constraint architecture rationale | `doc/SECURITY_ARCHITECTURE.md` |
| Builds, installation, and header-based modules         | `doc/BUILD_INSTALL.md`         |
| Module structure and development workflow              | `doc/GETTING_STARTED.md`       |
| Policy organization and ordering                       | `doc/STYLE_GUIDE.md`           |
| Interface and template names                           | `doc/INTERFACE_NAMING.md`      |
| Contribution, patch, and sign-off requirements         | `doc/HOW_TO_CONTRIBUTE.md`     |
| Installation and migration workflows                   | `doc/USE_REFPOLICY.md`         |

## Evidence and Uncertainty

- Inspect the relevant current code before answering questions or making changes.
- Read applicable specifications and authoritative documentation. Do not infer requirements from
  code alone when a specification governs behavior.
- Fetch web references directly from authoritative sources. Do not rely on cached search results,
  summaries, or snippets.
- Do not speculate. If authoritative sources are insufficient or conflict, state the uncertainty
  and ask the user before proceeding.

## Core Working Rules

- Keep changes focused on the requested policy module or build tool. Do not reformat unrelated
  policy.
- Follow `doc/STYLE_GUIDE.md` and the ordering of neighboring modules in the same layer.
- Prefer existing interfaces over direct `allow` rules against types owned by another module. Add
  or extend an interface in the owning module when necessary.
- Keep type declarations and local rules in `.te`, reusable public interfaces in `.if`, and path
  labeling expressions in `.fc`.
- Preserve optional-policy and tunable boundaries used by nearby rules.
- New Python code requires Python 3.10 or newer and should match the existing support-tool style.
- Format Markdown prose to at most 100 columns. Align Markdown tables, use spaces for indentation,
  and do not use hard tabs.
- Avoid `authorize` and its variants when `permission`, `access`, or `privilege` will work.

## Generated Files

Never edit generated policy, configuration, XML, HTML, or `tmp/` output directly. Change its source
and regenerate it.

In particular, change `policy/modules/kernel/corenetwork.te.in`, `corenetwork.if.in`, or
`corenetwork.if.m4` instead of generated `corenetwork.te` and `corenetwork.if` files. Do not edit
`policy.conf`, `file_contexts`, `homedir_template`, `doc/policy.xml`, `doc/tmp/`, or `doc/html/`.

## Required Skills

Use the following project skills whenever their trigger applies:

| Skill                              | Trigger                                                            |
|------------------------------------|--------------------------------------------------------------------|
| `refpolicy-validation`             | Validate any repository change                                     |
| `refpolicy-semantic-review`        | A change may alter compiled policy behavior                        |
| `refpolicy-constraints-change`     | Classes, permissions, common permissions, or constraints change    |
| `refpolicy-interface-authoring`    | Add, rename, extend, or review a public interface or template      |

See `refpolicy-validation` for the validation levels (targeted check, policy validation, semantic
review, CI-equivalent matrix) and which one applies to a given change; do not duplicate that list
here.

Policy source includes `.te`, `.if`, `.fc`, support macros, global booleans and tunables, users,
constraints, security classes, access vectors, and policy build configuration.

## Change Hygiene

- Review generated policy differences when a policy build changes behavior.
- Include related `.te`, `.if`, and `.fc` updates together when they form one policy feature.
- Keep each commit to one logical change and ensure the tree builds after each commit.
- Do not commit generated build artifacts.
- When asked to commit, verify the contributor's real name and include the required
  `Signed-off-by` trailer. Never invent contributor identity.
- Submit changes through a GitHub pull request as described in `doc/HOW_TO_CONTRIBUTE.md`.

## Reporting Results

- Report every validation command run and whether it passed or failed.
- State which checks could not run and why.
- Treat unavailable SETools or policy artifacts as an incomplete semantic review, not as an
  optional skipped check (see `refpolicy-validation` and `refpolicy-semantic-review` for reporting
  detail).
- Distinguish failures caused by the change from pre-existing worktree or environment failures.
