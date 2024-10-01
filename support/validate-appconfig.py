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

DBUS_CONTEXTS: typing.Final[str] = "dbus_contexts"
MEDIA_CONTEXTS: typing.Final[str] = "media"
SINGLE_LINE_CONTEXTS_FILES: typing.Final[tuple[str, ...]] = ("initrc_context",
                                                             "removable_context",
                                                             "userhelper_context")
LXC_CONTEXTS: typing.Final[str] = "lxc_contexts"
SEPGSQL_CONTEXTS: typing.Final[str] = "sepgsql_contexts"
VIRT_CONTEXTS_FILES: typing.Final[tuple[str, ...]] = ("virtual_domain_context",
                                                      "virtual_image_context")
XSERVER_CONTEXTS: typing.Final[str] = "x_contexts"

CHKCON_PATHS: typing.Final[tuple[Path, ...]] = (Path("/usr/local/bin"),
                                                Path("/usr/local/sbin"),
                                                Path("/usr/bin"),
                                                Path("/bin"),
                                                Path("/usr/sbin"),
                                                Path("/sbin"))


class ContextValidator:

    """Validate contexts using security_check_context or chkcon"""

    def __init__(self, /, policy_path: str | None = None, *,
                 chkcon_path: str | None = None) -> None:

        self.log = logging.getLogger(self.__class__.__name__)
        self.policy_path = policy_path
        self.selinux_enabled = libselinux.is_selinux_enabled() == 1
        self.chkcon_path: Path | str | None = self._find_chkcon(chkcon_path)
        self.log.debug(f"{self.__class__.__name__}: "
                       f"{self.policy_path=}, "
                       f"{self.selinux_enabled=}, "
                       f"{self.chkcon_path=}")

    def _find_chkcon(self, /, path: Path | str | None) -> Path | str | None:
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

    def validate_context(self, context: str, /) -> bool:
        """Verify that the specified context is valid in the policy."""
        if self.chkcon_path and self.policy_path:
            self.log.debug(f"Validating context {context} with chkcon")
            return self._chkcon_check_context(context)

        if self.selinux_enabled:
            self.log.debug(f"Validating context {context} with security_check_context")
            return libselinux.security_check_context(context) == 0

        self.log.critical(f"Warning: Context validation not done for {context}")
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
    logging.info(f"Using {minidom.__name__} for parsing {file_path}.")
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
            print(f"Invalid element found under <selinux>: {child.toxml()}")
            valid = False
            continue

        # Validate that each <associate> element has only "own" and "context" attributes
        attributes: minidom.NamedNodeMap = child.attributes
        if set(attributes.keys()) != {"own", "context"}:
            print(f"Invalid associate element: {child.toxml()}")
            valid = False
            continue

        # Validate the context attribute
        own: str = attributes["own"].value
        context: str = attributes["context"].value
        if not validator.validate_context(context):
            print(f"Invalid context for service {own}: {context}")
            valid = False

    return valid


def validate_lxc_contexts(validator: ContextValidator, fullpath: Path, /) -> bool:
    """Validate the lxc_contexts file."""
    valid: bool = True
    with open(fullpath, "r", encoding="utf-8") as file:
        logging.info(f"Validating {fullpath}")
        for line in file:
            line = line.strip()
            items = line.split()
            with suppress(IndexError):
                if not items:
                    continue

                context = items[2].strip("\"")
                if not validator.validate_context(context):
                    print(f"Invalid context in {fullpath}: {line}")
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
    valid: bool = True
    for filename in filenames:
        with open(filename, "r", encoding="utf-8") as file:
            logging.info(f"Validating {filename}")
            for line in file:
                line = line.strip()
                if not line:
                    continue

                if not validator.validate_context(line):
                    print(f"Invalid context in {filename}: {line}")
                    valid = False

    return valid


def validate_media_contexts(validator: ContextValidator, fullpath: Path, /) -> bool:
    """Validate the contexts in the media file."""
    valid: bool = True
    with open(fullpath, "r", encoding="utf-8") as file:
        logging.info(f"Validating {fullpath}")
        for line in file:
            line = line.strip()
            with suppress(IndexError):
                if not validator.validate_context(line.split()[1]):
                    print(f"Invalid context in {fullpath}: {line}")
                    valid = False

    return valid


def validate_three_field_contexts(validator: ContextValidator, filepaths: list[Path], /,
                                  comment_char: str = "#") -> bool:
    """
    Validate the contexts of a file that has three fields per line, with
    the third field being the context.  Examples are sepgsql_contexts and
    x_contexts.
    """
    valid: bool = True

    for fullpath in filepaths:
        with open(fullpath, "r", encoding="utf-8") as file:
            logging.info(f"Validating {fullpath}")
            for line in file:
                line = line.strip()
                items = line.split()
                with suppress(IndexError):
                    if not items or items[0].startswith(comment_char):
                        continue

                    if not validator.validate_context(items[2]):
                        print(f"Invalid context in {fullpath}: {line}")
                        valid = False

    return valid


def validate_appconfig_files(conf_dir: str, /, *,
                             policy_path: str | None = None,
                             chkcon_path: str | None = None,
                             lxc: bool = True,
                             sepgsql: bool = True,
                             virt: bool = True,
                             xserver: bool = True) -> bool:

    """Validate the various appconfig userspace config files."""
    validator: typing.Final[ContextValidator] = ContextValidator(policy_path=policy_path,
                                                                 chkcon_path=chkcon_path)
    base_path: typing.Final[Path] = Path(conf_dir)

    single_line_contexts = [base_path / p for p in SINGLE_LINE_CONTEXTS_FILES]
    if virt:
        single_line_contexts.extend(base_path / p for p in VIRT_CONTEXTS_FILES)

    key_value_contexts = list[Path]()
    if sepgsql:
        key_value_contexts.append(base_path / SEPGSQL_CONTEXTS)
    if xserver:
        key_value_contexts.append(base_path / XSERVER_CONTEXTS)

    return all((validate_dbus_contexts(validator, base_path / DBUS_CONTEXTS),
                validate_single_line_context_files(validator, single_line_contexts),
                validate_media_contexts(validator, base_path / MEDIA_CONTEXTS),
                validate_three_field_contexts(validator, key_value_contexts),
                validate_lxc_contexts(validator, base_path / LXC_CONTEXTS) if lxc else True))


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

    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s|%(levelname)s|%(name)s|%(message)s')
        if not sys.warnoptions:
            warnings.simplefilter("default")
    else:
        logging.basicConfig(level=logging.WARNING, format='%(message)s')
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
