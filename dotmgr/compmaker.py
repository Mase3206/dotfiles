#!/usr/bin/env python3

"""
NOTE: This completion maker is tailor-made to my setup.
"""

from __future__ import annotations

import shlex
from argparse import ArgumentParser, _SubParsersAction
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Optional, Union


@dataclass
class Command:
    name: str
    help: str
    description: str
    positionals: list[Argument]
    optionals: list[Argument]
    subcommands: list[Command]
    epilog: Optional[str] = ""
    # aliases: list[str]  # Aliases are not supported at this time.

    @property
    def __dict__(self) -> dict:
        return {
            "name": self.name,
            "help": self.help,
            "description": self.description,
            "positionals": [arg.__dict__ for arg in self.positionals],
            "optionals": [arg.__dict__ for arg in self.optionals],
            "subcommands": [arg.__dict__ for arg in self.subcommands],
            "epilog": self.epilog,
        }


class NargType(Enum):
    ONE_OR_NONE = "?"
    AT_LEAST_ONE = "+"
    ANY_AMOUNT = "*"
    ZERO = 0
    UNSET = None


@dataclass
class Argument:
    name: str
    flags: list[str]
    required: bool
    help: str
    nargs: NargType = NargType.UNSET
    default: Optional[Union[Iterable, Any]] = field(default_factory=list)
    choices: Optional[Iterable] = field(default_factory=list)
    choices_shell_updater: Optional[str] = None

    @property
    def __dict__(self) -> dict:
        default_value = _iterable_to_list(self.default)
        choices_value = _iterable_to_list(self.choices)
        return {
            "name": self.name,
            "flags": self.flags,
            "required": self.required,
            "help": self.help,
            "nargs": self.nargs.value,
            "default": default_value,
            "choices": choices_value,
            "choices_shell_updater": self.choices_shell_updater,
        }


def _iterable_to_list(value: Any) -> Any:
    if value is None:
        return None
    if type(value).__name__ == "dict_keys":
        return list(value)
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return value


def _normalize_nargs(nargs: Any) -> NargType:
    try:
        return NargType(nargs)
    except ValueError:
        return NargType.UNSET


def _help_text(text: Any) -> str:
    value = str(text) if text else "(no help defined)"
    return value.replace("%", "%%").replace("[", "\\[").replace("]", "\\]")


def _choice_updater(choices: Any) -> Optional[str]:
    return getattr(choices, "dynamic_shell", None)


def action_to_field(action: Any) -> Argument:
    """Normalize an argparse action into a compact, shell-friendly field."""
    return Argument(
        name=str(action.metavar if action.metavar else action.dest),
        flags=list(getattr(action, "option_strings", [])),
        required=bool(getattr(action, "required", False)),
        help=_help_text(getattr(action, "help", None)),
        nargs=_normalize_nargs(getattr(action, "nargs", None)),
        default=_iterable_to_list(getattr(action, "default", None)),
        choices=_iterable_to_list(getattr(action, "choices", None)),
        choices_shell_updater=_choice_updater(getattr(action, "choices", None)),
    )


def _shell_word(value: str) -> str:
    return shlex.quote(value)


def _choice_list(values: Iterable[Any]) -> str:
    return "(" + " ".join(_shell_word(str(value)) for value in values) + ")"


def _description_choice_list(values: Iterable[tuple[str, str]]) -> str:
    return "((" + " ".join(_shell_word(f"{name}:{description}") for name, description in values) + "))"


def _argument_action(field: Argument, helper_name: Optional[str]) -> str:
    if helper_name:
        return helper_name
    if field.choices:
        return _choice_list(field.choices)
    if field.name.lower() in {"file", "path", "dir", "directory"}:
        return "_files"
    return ""


def _argument_spec(field: Argument, helper_name: Optional[str] = None) -> str:
    action = _argument_action(field, helper_name)

    if field.flags:
        option = field.flags[0]
        if field.nargs == NargType.ZERO:
            return f"{_shell_word(option)}[{field.help}]"
        if field.nargs == NargType.ONE_OR_NONE:
            if action:
                return f"{_shell_word(option)}[{field.help}]::{field.name}:{action}"
            return f"{_shell_word(option)}[{field.help}]::{field.name}:"
        if action:
            return f"{_shell_word(option)}[{field.help}]:{field.name}:{action}"
        return f"{_shell_word(option)}[{field.help}]:{field.name}:"

    if field.nargs == NargType.ONE_OR_NONE:
        prefix = "::"
    elif field.nargs in {NargType.AT_LEAST_ONE, NargType.ANY_AMOUNT}:
        prefix = "*:"
    else:
        prefix = ":"

    return f"{prefix}{field.name}:{action}" if action else f"{prefix}{field.name}:"


def _dispatch_helper_name(parent_name: str, child_name: str) -> str:
    return f"_{parent_name.lstrip('_')}__{child_name}"


def _choice_helper_name(function_name: str, field_name: str) -> str:
    return f"_{function_name.lstrip('_')}__{field_name}_choices"


def _render_choice_helper(helper_name: str, updater: str) -> str:
    return f"""{helper_name}() {{
  local -a values
  values=("${{(@f)$({updater} | tr '\\0' '\\n')}}")
  compadd -- "${{values[@]}}"
}}"""


def _render_subcommand_choices(command: Command) -> str:
    return _description_choice_list((subcommand.name, subcommand.help) for subcommand in command.subcommands)


def _render_command(
    command: Command,
    function_name: str,
    command_defs: list[str],
    helper_defs: list[str],
    helper_lookup: dict[str, str],
) -> None:
    lines: list[str] = [f"{function_name}() {{"]

    if command.subcommands:
        lines.extend([
            "  local subcommand",
            "  if (( CURRENT > 2 )) && [[ -n ${words[2]} ]]; then",
            "    subcommand=${words[2]}",
            "    compset -n 2",
            "    case $subcommand in",
        ])

        for subcommand in command.subcommands:
            child_function = _dispatch_helper_name(command.name, subcommand.name)
            lines.extend([
                f"      ({subcommand.name})",
                f"        {child_function}",
                "        return",
                "        ;;",
            ])

        lines.extend([
            "    esac",
            "  fi",
            "",
        ])

    lines.append("  _arguments -C " + "\\")

    specs: list[str] = []

    if command.subcommands:
        specs.append(f"1:command:{_render_subcommand_choices(command)}")

    for field in command.optionals + command.positionals:
        helper_name = None
        if field.choices_shell_updater:
            helper_name = helper_lookup.get(field.choices_shell_updater)
            if helper_name is None:
                helper_name = _choice_helper_name(function_name, field.name)
                helper_lookup[field.choices_shell_updater] = helper_name
                helper_defs.append(_render_choice_helper(helper_name, field.choices_shell_updater))
        specs.append(_argument_spec(field, helper_name))

    if specs:
        for index, spec in enumerate(specs):
            continuation = " " + "\\" if index < len(specs) - 1 else ""
            lines.append(f"    {shlex.quote(spec)}{continuation}")
    else:
        lines.append("    --")

    lines.append("}")
    command_defs.append("\n".join(lines))

    for subcommand in command.subcommands:
        _render_command(
            subcommand,
            _dispatch_helper_name(command.name, subcommand.name),
            command_defs,
            helper_defs,
            helper_lookup,
        )


def render_zsh(command: Command) -> str:
    """Render an autoloadable zsh completion file for the parsed command tree."""
    command_defs: list[str] = []
    helper_defs: list[str] = []
    helper_lookup: dict[str, str] = {}

    _render_command(command, f"_{command.name}", command_defs, helper_defs, helper_lookup)

    parts: list[str] = [f"#compdef {command.name}", ""]
    if helper_defs:
        parts.append("\n\n".join(helper_defs))
        parts.append("")
    parts.append("\n\n".join(command_defs))
    parts.append("")
    return "\n".join(parts)


def convert_from_parser(
    parser: ArgumentParser,
    cmd_name: Optional[str] = None,
    help_str: str = "",
) -> Command:

    if not cmd_name:
        cmd_name = parser.prog.split(" ")[-1]

    cmd_epilog = parser.epilog
    cmd_description = parser.description if parser.description else help_str

    cmd_subcommands: list[Command] = []
    cmd_positionals: list[Argument] = []
    cmd_optionals: list[Argument] = []

    _cmd_positional_actions = parser._get_positional_actions()
    for _action in _cmd_positional_actions:
        if isinstance(_action, _SubParsersAction):
            cmd_help_strings: dict[str, str] = {
                cpa.metavar: cpa.help
                for cpa in parser._get_positional_actions()[0]._choices_actions  # type: ignore
            }
            for c_name, c_parser in _action.choices.items():  # type: ignore
                cmd_subcommands.append(
                    convert_from_parser(
                        c_parser,
                        c_name,
                        cmd_help_strings[c_name],
                    )
                )
        else:
            cmd_positionals.append(action_to_field(_action))

    for opt_act in parser._get_optional_actions():
        cmd_optionals.append(action_to_field(opt_act))

    return Command(
        name=cmd_name,
        help=help_str,
        description=cmd_description,
        positionals=cmd_positionals,
        optionals=cmd_optionals,
        subcommands=cmd_subcommands,
        epilog=cmd_epilog,
    )


if __name__ == "__main__":
    from dotmgr.dot import parser  # noqa: I001
    import json

    commands = convert_from_parser(parser, cmd_name="dot")
    print(json.dumps(commands.__dict__))
    # print(render_zsh(commands))
