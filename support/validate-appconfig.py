#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
"""Validate refpolicy userpace configuration files (appconfig) have valid contexts."""

import argparse
from contextlib import suppress
import logging
import os
from pathlib import Path
import subprocess
import sys
import typing
import warnings
from xml.dom.minidom import Node

try:
    from defusedxml import minidom
except ImportError:
    from xml.dom import minidom

import selinux as libselinux

with suppress(ImportError):
    import setools

DBUS_CONTEXTS: typing.Final[str] = "dbus_contexts"
DEFAULT_CONTEXTS: typing.Final[str] = "default_contexts"
DEFAULT_TYPE: typing.Final[str] = "default_type"
MEDIA_CONTEXTS: typing.Final[str] = "media"
SINGLE_LINE_PARTIAL_CONTEXTS_FILES: typing.Final[tuple[str, ...]] = ("failsafe_context",)
SINGLE_LINE_CONTEXTS_FILES: typing.Final[tuple[str, ...]] = ("initrc_context",
                                                             "removable_context",
                                                             "userhelper_context")
LXC_CONTEXTS: typing.Final[str] = "lxc_contexts"
SEPGSQL_CONTEXTS: typing.Final[str] = "sepgsql_contexts"
SEUSER_DEFAULT_CONTEXTS_GLOB: typing.Final[str] = f"*_{DEFAULT_CONTEXTS}"
VIRT_CONTEXTS_FILES: typing.Final[tuple[str, ...]] = ("virtual_domain_context",
                                                      "virtual_image_context")
XSERVER_CONTEXTS: typing.Final[str] = "x_contexts"

CHKCON_PATHS: typing.Final[tuple[Path, ...]] = (Path("/usr/local/bin"),
                                                Path("/usr/local/sbin"),
                                                Path("/usr/bin"),
                                                Path("/bin"),
                                                Path("/usr/sbin"),
                                                Path("/sbin"))

GITHUB_ACTIONS_ENV_VAR: typing.Final[str] = "GITHUB_ACTION"


class ContextValidator:

    """Validate contexts using security_check_context or chkcon"""

    def __init__(self, /, policy_path: typing.Optional[str]= None, *,
                 chkcon_path: typing.Optional[str] = None) -> None:

        self.log = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.selinux_enabled = libselinux.is_selinux_enabled() == 1
        self.policy_path = policy_path
        self.chkcon_path: typing.Optional[Path, str, None] = self._find_chkcon(chkcon_path)
        try:
            self.policy = setools.SELinuxPolicy(policy_path) \
                if self.selinux_enabled or policy_path else None
            self.dta = setools.DomainTransitionAnalysis(self.policy,
                                                        mode = setools.DomainTransitionAnalysis.Mode.AllPaths,
                                                        depth_limit = 1) \
                                                        if self.policy else None
            self.rbacrq = setools.RBACRuleQuery(self.policy,
                                                ruletype = (setools.RBACRuletype.allow,)) \
                                                if self.policy else None
        except NameError:
            self.policy = None
            self.dta = None
            self.rbacrq = None
            self.log.warning(f"SETools not available. {sys.path=}")
        except AttributeError:
            self.dta = None
            self.rbacrq = None
            self.log.warning(f"Old SETools Available - partial analysis only. {sys.path=}")

        self.log.debug(f"{self.__class__.__name__}: "
                       f"{self.selinux_enabled=}, "
                       f"{self.policy_path=}, "
                       f"{self.policy=}, "
                       f"{self.chkcon_path=}")

    def _find_chkcon(self, /, path: typing.Union[Path, str, None]) -> typing.Union[Path, str,  None]:
        if path:
            self.log.debug(f"Checking access on provided chkcon path {path}")
            if os.access(path, os.X_OK):
                return path

        for p in CHKCON_PATHS:
            path = p / "chkcon"
            self.log.debug(f"Trying chkcon path {path}")
            if os.access(path, os.X_OK):
                return path

        self.log.warning("chkcon not found, trying to find with \"which\"")
        result = subprocess.run(["which", "chkcon"],
                                check=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return result.stdout.decode().strip() if result.returncode == 0 else None

    def _chkcon_check_context(self, context: str, /) -> bool:
        assert self.chkcon_path
        assert self.policy_path
        result = subprocess.run([self.chkcon_path, self.policy_path, context],
                                check=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        return result.returncode == 0

    def validate_user(self, user: str, /) -> bool:
        """Validate the specified user."""
        if not self.policy:
            self.log.warning(f"User validation not done for {user}")
            return True

        try:
            _ = self.policy.lookup_user(user)
        except setools.exception.InvalidSymbol:
            return False

        return True

    def validate_role_type(self, context: str, /) -> bool:
        """Validate role:type associations"""
        if not self.policy:
            self.log.warning(f"Role:type context validation not done for {context}")
            return True

        ctx = context.split(":")
        if len(ctx) != 2 or not all(ctx):
            return False

        try:
            role = self.policy.lookup_role(ctx[0])
            type_ = self.policy.lookup_type(ctx[1])

            if type_ not in set(role.types()):
                self.log.debug(f"Type {type_} not in role {role}")
                return False

            return True

        except setools.exception.InvalidSymbol as e:
            self.log.debug(str(e))
            return False

    def validate_domain_transition(self, source_domain: str, target_domain: str, /) -> bool:
        """Validate a domain transition (RBAC and TE only) is allowed in the policy"""
        # in this function source/target domain refers to the role:type[:level] context
        # and source/target type refers to only the type.
        valid: bool = True
        try:
            if not self.rbacrq or not self.dta:
                self.log.warning(f"Domain transition not done for {source_domain} -> {target_domain}")
                return True

            self.log.debug(f"Validating domain transition {source_domain} -> {target_domain}")
            source_role, source_type = source_domain.split(":")[0:2]
            target_role, target_type = target_domain.split(":")[0:2]

            #
            # Validate role change
            #
            if source_role == target_role:
                self.log.debug(f"No role change ({source_role} -> {target_role}).")
            else:
                self.rbacrq.source = source_role
                self.rbacrq.target = target_role

                try:
                    # only need to find 1 valid result.
                    _ = next(self.rbacrq.results())
                    self.log.debug(f"Role change {source_role} -> {target_role} is allowed.")
                except StopIteration:
                    self.log.debug(f"Role change {source_role} -> {target_role} is NOT allowed.")
                    valid = False

            #
            # Vaidate domain (TE) transition
            #
            if source_type == target_type:
                # unlikely
                self.log.debug(f"No type change ({source_type} -> {target_type}).")
            else:
                self.dta.source = source_type
                self.dta.target = target_type

                try:
                    # only need to find 1 valid result.
                    _ = next(self.dta.results())
                    self.log.debug(f"Domain transition {source_domain} -> {target_domain} is allowed.")
                except StopIteration:
                    self.log.debug(f"Domain transition {source_domain} -> {target_domain} is NOT allowed.")
                    valid = False

        except setools.exception.InvalidSymbol as e:
            self.log.debug(str(e))
            valid = False

        return valid

    def validate_partial_context(self, context: str, /) -> bool:
        """Validate a partial context (no seuser)"""
        if not self.policy:
            self.log.warning(f"Partial context validation not done for {context}")
            return True

        self.log.info(f"Validating partial context {context}")

        ctx = context.split(":")
        if (self.policy.mls and len(ctx) != 3) or (not self.policy.mls and len(ctx) != 2) \
                or not all(ctx):

            self.log.debug(f"Incorrect number of fields in {context}")
            return False

        try:
            # default level and clearance are tied to seuser, so ensuring
            # the level is valid is the only possible check here.
            _ = self.policy.lookup_level(ctx[2]) if self.policy.mls else None

            return self.validate_role_type(":".join(ctx[:2]))

        except setools.exception.InvalidSymbol as e:
            self.log.debug(str(e))
            return False

    def validate_context(self, context: str, /) -> bool:
        """Verify that the specified context is valid in the policy."""
        if self.chkcon_path and self.policy_path:
            self.log.debug(f"Validating context {context} with chkcon")
            return self._chkcon_check_context(context)

        if self.selinux_enabled:
            self.log.debug(f"Validating context {context} with security_check_context")
            return libselinux.security_check_context(context) == 0

        self.log.warning(f"Context validation not done for {context}")
        return True


def validate_dbus_contexts(validator: ContextValidator, file_path: Path, /) -> bool:
    """
    Validate the contexts in the specified dbus_contexts file.

    A minimum/empty dbus_contexts file is as follows:

    <busconfig>
      <selinux>
      </selinux>
    </busconfig>

    An example dbus_contexts with dbus service labeling:

    <busconfig>
      <selinux>
        <associate own="org.selinux.semanage" context="system_u:system_r:selinux_dbus_t:s0" />
        <associate own="org.selinux.Restorecond" context="system_u:system_r:restorecond_t:s0" />
      </selinux>
    </busconfig>
    """

    # Parse the XML file
    log = logging.getLogger(__name__).getChild("validate_dbus_contexts")
    log.info(f"Using {minidom.__name__} for parsing {file_path}.")
    dom: typing.Final[minidom.Document] = minidom.parse(str(file_path))

    # Ensure <busconfig> is the top-level tag
    top_level_elements: list[minidom.Element] = [node for node in dom.childNodes
                                                 if node.nodeType == Node.ELEMENT_NODE]

    if len(top_level_elements) != 1 or top_level_elements[0].tagName != "busconfig":
        raise ValueError("The top-level tag must be <busconfig>.")

    busconfig = top_level_elements[0]

    # Not validating that <selinux> is the only tag under <busconfig> as other
    # tags can work, such as <policy>.
    selinux_elements: list[minidom.Element] = [node for node in busconfig.childNodes
                                               if node.nodeType == Node.ELEMENT_NODE
                                               and node.tagName == "selinux"]

    # Ensure there is only one <selinux> element
    if len(selinux_elements) != 1:
        raise ValueError(
            f"Invalid number of <selinux> elements found under <busconfig>: {selinux_elements}.")

    # Check if all child nodes are <associate> elements
    valid: bool = True
    for child in selinux_elements[0].childNodes:
        if child.nodeType != Node.ELEMENT_NODE:
            continue

        if child.tagName != "associate":
            log.error(f"Invalid element found under <selinux>: {child.toxml()}")
            valid = False
            continue

        # Validate that each <associate> element has only "own" and "context" attributes
        attributes: minidom.NamedNodeMap = child.attributes
        if set(attributes.keys()) != {"own", "context"}:
            log.error(f"Invalid associate element: {child.toxml()}")
            valid = False
            continue

        # Validate the context attribute
        own: str = attributes["own"].value
        context: str = attributes["context"].value
        if not validator.validate_context(context):
            log.error(f"Invalid context for service {own}: {context}")
            valid = False
            continue

    return valid


def validate_lxc_contexts(validator: ContextValidator, fullpath: Path, /) -> bool:
    """Validate the lxc_contexts file."""
    log = logging.getLogger(__name__).getChild("validate_lxc_contexts")
    valid: bool = True
    with open(fullpath, "r", encoding="utf-8") as file:
        log.info(f"Validating {fullpath}")
        for line in file:
            line = line.strip()
            items = line.split()
            with suppress(IndexError):
                if not items:
                    continue

                context = items[2].strip("\"")
                if not validator.validate_context(context):
                    log.error(f"Invalid context in {fullpath}: {line}")
                    valid = False

    return valid


def validate_default_type(validator: ContextValidator, filename: Path, /) -> bool:
    """
    Validate the default_type file.  This file always has role:type pairs,
    and never has MLS levels.

    Validation is looser here than for other appconfig files.  The files are not
    changed based on the modules in the policy, since invalid contexts
    are not fatal to the userspace code.
    """
    log = logging.getLogger(__name__).getChild("validate_default_type")
    valid_lines: int = 0
    with open(filename, "r", encoding="utf-8") as file:
        log.info(f"Validating {filename}")
        for line in file:
            line = line.strip()
            if not line:
                continue

            if validator.validate_role_type(line):
                valid_lines += 1
            else:
                log.warning(f"Invalid context in {filename}: {line}")

    return valid_lines > 0


def validate_single_line_partial_context_files(validator: ContextValidator,
                                               filenames: list[Path], /) -> bool:
    """
    Validate the contexts in the files with a single partial context per line,
    such as failsafe_context.
    """
    log = logging.getLogger(__name__).getChild("validate_single_line_partial_context_files")
    valid: bool = True
    for filename in filenames:
        with open(filename, "r", encoding="utf-8") as file:
            log.info(f"Validating {filename}")
            for line in file:
                line = line.strip()
                if not line:
                    continue

                if not validator.validate_partial_context(line):
                    log.error(f"Invalid context in {filename}: {line}")
                    valid = False

    return valid


def validate_single_line_context_files(validator: ContextValidator,
                                       filenames: list[Path], /) -> bool:
    """
    Validate the contexts in the files with single context per line.  This
    is primarily for files tha have a single context, such as initrc_context,
    but can also be used for virtual_image_context, which can have multiple
    lines of a single context.
    """
    log = logging.getLogger(__name__).getChild("validate_single_line_context_files")
    valid: bool = True
    for filename in filenames:
        with open(filename, "r", encoding="utf-8") as file:
            log.info(f"Validating {filename}")
            for line in file:
                line = line.strip()
                if not line:
                    continue

                if not validator.validate_context(line):
                    log.error(f"Invalid context in {filename}: {line}")
                    valid = False

    return valid


def validate_media_contexts(validator: ContextValidator, fullpath: Path, /) -> bool:
    """Validate the contexts in the media file."""
    log = logging.getLogger(__name__).getChild("validate_media_contexts")
    valid: bool = True
    with open(fullpath, "r", encoding="utf-8") as file:
        log.info(f"Validating {fullpath}")
        for line in file:
            line = line.strip()
            with suppress(IndexError):
                if not validator.validate_context(line.split()[1]):
                    log.error(f"Invalid context in {fullpath}: {line}")
                    valid = False

    return valid


def validate_three_field_contexts(validator: ContextValidator, filepaths: list[Path], /,
                                  comment_char: str = "#") -> bool:
    """
    Validate the contexts of a file that has three fields per line, with
    the third field being the context.  Examples are sepgsql_contexts and
    x_contexts.
    """
    log = logging.getLogger(__name__).getChild("validate_three_field_contexts")
    valid: bool = True

    for fullpath in filepaths:
        with open(fullpath, "r", encoding="utf-8") as file:
            log.info(f"Validating {fullpath}")
            for line in file:
                line = line.strip()
                items = line.split()
                with suppress(IndexError):
                    if not items or items[0].startswith(comment_char):
                        continue

                    if not validator.validate_context(items[2]):
                        log.error(f"Invalid context in {fullpath}: {line}")
                        valid = False

    return valid


def _validate_default_contexts_line(validator: ContextValidator, line: str,
                                    /, seuser: str = "") -> tuple[str, list[str], list[str]]:
    """Validate a single line of default_contexts, optionally apply seuser to target domains."""
    log = logging.getLogger(__name__).getChild("_validate_default_contexts_line")
    columns = [c for c in line.split() if c]
    source_domain: str = columns[0]
    target_domains: list[str] = columns[1:]
    valid_target_domains: list[str] = []
    invalid_target_domains: list[str] = []

    if not validator.validate_partial_context(source_domain):
        raise ValueError(f"Invalid source domain: {source_domain}.")

    if seuser:
        validate_function = lambda x: validator.validate_context(f"{seuser}:{x}")
    else:
        validate_function = validator.validate_partial_context

    for target_domain in target_domains:
        if not validate_function(target_domain):
            log.debug(f"Invalid target domain: {source_domain}: {target_domain}")
            invalid_target_domains.append(target_domain)
            continue

        if not validator.validate_domain_transition(source_domain, target_domain):
            log.debug(f"Invalid domain transition: {source_domain} -> {target_domain}")
            invalid_target_domains.append(target_domain)
            continue

        valid_target_domains.append(target_domain)

    return source_domain, valid_target_domains, invalid_target_domains


def validate_default_contexts(validator: ContextValidator, default_contexts: Path,
                              seuser_default_contacts: list[Path], /) -> bool:

    """
    Validate all default_context files.

    Validation is looser here than for other appconfig files.  The files are not
    changed based on the modules in the policy, since invalid contexts
    are not fatal to the userspace code.

    While these files rarely change, debugging issues with changing them can be
    challenging, so this does enhanced checking to attempt to verify that the
    domain transitions are valid.  However, this is not a guarantee since the
    seuser is not available on the source domain and constraints are not
    checked.
    """

    log = logging.getLogger(__name__).getChild("validate_default_contexts")
    valid: bool = True
    valid_source_domains: dict[str, list[str]] = {}

    #
    # Validate the default_contexts file. This must have at least one valid line.
    #
    with open(default_contexts, "r", encoding="utf-8") as file:
        log.info(f"Validating {default_contexts}")
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                source_domain, valid_target_domains, invalid_target_domains = \
                    _validate_default_contexts_line(validator, line)

                if valid_target_domains:
                    valid_source_domains[source_domain] = valid_target_domains
                else:
                    log.warning(f"{default_contexts}: No valid target domains " \
                                f"for {source_domain}")

            except ValueError as e:
                log.warning(f"{default_contexts}: {e}")

    log.debug(f"{default_contexts}: Valid source domains: {valid_source_domains}")
    if not valid_source_domains:
        valid = False

    #
    # Validate *_default_contexts files.
    #
    # refpolicy has a number of *_default_contexts files that are used to customize
    # the default contexts behavior for a particular seuser.  These files are
    # named "<seuser>_default_contexts" and have the same format as default_contexts.
    #
    for filepath in seuser_default_contacts:
        valid_lines: int = 0
        seuser = filepath.name.rsplit("_", 2)[0]
        log.info(f"Validating {filepath} for seuser {seuser}")

        if not validator.validate_user(seuser):
            log.warning(f"{filepath}: Invalid user {seuser}: Skipping validation.")
            continue

        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    source_domain, valid_target_domains, invalid_target_domains = \
                        _validate_default_contexts_line(validator, line, seuser=seuser)

                    if source_domain not in valid_source_domains:
                        # could be intentional; can't say for sure this is an error
                        log.warning(f"{filepath}: Source domain {source_domain} " \
                                    "not in default_contexts.")

                    if not valid_target_domains:
                        log.warning(f"{filepath}: No valid target domains " \
                                    f"for {source_domain}")
                        continue

                    valid_lines += 1

                except ValueError as e:
                    log.warning(f"{filepath}: {e}")
                    continue

        if not valid_lines:
            log.error(f"{filepath}: No valid lines.")
            valid = False

    return valid


def validate_appconfig_files(conf_dir: str, /, *,
                             policy_path: typing.Optional[str] = None,
                             chkcon_path: typing.Optional[str] = None,
                             lxc: bool = True,
                             sepgsql: bool = True,
                             virt: bool = True,
                             xserver: bool = True) -> bool:

    """Validate the various appconfig userspace config files."""
    validator: typing.Final[ContextValidator] = ContextValidator(policy_path=policy_path,
                                                                 chkcon_path=chkcon_path)
    base_path: typing.Final[Path] = Path(conf_dir)

    single_line_partial_contexts = [base_path / p for p in SINGLE_LINE_PARTIAL_CONTEXTS_FILES]

    single_line_contexts = [base_path / p for p in SINGLE_LINE_CONTEXTS_FILES]
    if virt:
        single_line_contexts.extend(base_path / p for p in VIRT_CONTEXTS_FILES)

    key_value_contexts = list[Path]()
    if sepgsql:
        key_value_contexts.append(base_path / SEPGSQL_CONTEXTS)
    if xserver:
        key_value_contexts.append(base_path / XSERVER_CONTEXTS)

    seuser_default_contexts = list(base_path.glob(SEUSER_DEFAULT_CONTEXTS_GLOB))

    return all((validate_dbus_contexts(validator, base_path / DBUS_CONTEXTS),
                validate_single_line_context_files(validator, single_line_contexts),
                validate_media_contexts(validator, base_path / MEDIA_CONTEXTS),
                validate_three_field_contexts(validator, key_value_contexts),
                validate_lxc_contexts(validator, base_path / LXC_CONTEXTS) if lxc else True,
                validate_default_type(validator, base_path / DEFAULT_TYPE),
                validate_single_line_partial_context_files(validator,
                                                           single_line_partial_contexts),
                validate_default_contexts(validator, base_path / DEFAULT_CONTEXTS,
                                          seuser_default_contexts)))


class GitHubFormatter(logging.Formatter):

    """Optionally format log messages for GitHub Actions."""

    def __init__(self, *pargs, **kwargs) -> None:
        super().__init__(*pargs, **kwargs)
        self.github: bool = os.getenv(GITHUB_ACTIONS_ENV_VAR) is not None

    def format(self, record: logging.LogRecord) -> str:
        if self.github:
            formatted = super().format(record)
            if record.levelno <= logging.DEBUG:
                return f"::debug::{formatted}"
            elif record.levelno <= logging.INFO:
                return f"::notice::{formatted}"
            elif record.levelno <= logging.WARNING:
                return f"::warning::{formatted}"
            else:
                return f"::error::{formatted}"
        else:
            record.msg = f"{record.levelname.lower()}: {record.msg}"

        return super().format(record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate userspace app config.",
        epilog="If no policy is specified, the running policy (if any) is used.")
    parser.add_argument("APPCONFIG_DIR", type=str,
                        help="Path to the appconfig dir to validate")
    parser.add_argument("POLICY_PATH", nargs="?", type=str,
                        help="Path to binary policy file (optional)")
    parser.add_argument("-c", "--chkcon", type=str,
                        help="Path to chkcon executable.")
    parser.add_argument("-l", "--lxc", action="store_true", help="Check lxc_contexts.")
    parser.add_argument("-s", "--sepgsql", action="store_true", help="Check sepgsql_contexts.")
    parser.add_argument("-v", "--virt", action="store_true", help="Check virtual_*_context.")
    parser.add_argument("-x", "--xserver", action="store_true", help="Check x_contexts.")
    parser.add_argument("--debug", action="store_true", dest="debug",
                        help="Enable debugging.")
    args = parser.parse_args()

    handler = logging.StreamHandler(sys.stdout)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, handlers=(handler,))
        handler.setFormatter(GitHubFormatter("%(asctime)s|%(levelname)s|%(name)s|%(message)s"))

        if not sys.warnoptions:
            warnings.simplefilter("default")
    else:
        logging.basicConfig(level=logging.WARNING, handlers=(handler,))
        handler.setFormatter(GitHubFormatter("%(message)s"))

        if not sys.warnoptions:
            warnings.simplefilter("ignore")

    try:
        # Validate the <associate> elements under <selinux>
        sys.exit(0 if validate_appconfig_files(args.APPCONFIG_DIR,
                                       	       policy_path=args.POLICY_PATH,
                                               chkcon_path=args.chkcon,
                                               lxc=args.lxc,
                                               sepgsql=args.sepgsql,
                                               virt=args.virt,
                                               xserver=args.xserver) else 1)

    except Exception as err:
        if args.debug:
            raise

        print(err)
        sys.exit(1)
