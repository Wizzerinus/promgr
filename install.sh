#!/usr/bin/env bash

TERMI="$TERM"
# workaround for kitty naming itself wrongly
if [ "$TERMI" = "xterm-kitty" ]; then TERMI=kitty; fi

read -p "Enter template folder (default: $HOME/promgr/templates): " TPL_FOLDER
read -p "Enter folder to store projects in (default: $HOME/promgr/work): " WORK_FOLDER
read -p "Enter default text editor (default: $TERMI $EDITOR): " DEFAULT_EDITOR

TPL_FOLDER="${TPL_FOLDER:-$HOME/promgr/templates}"
WORK_FOLDER="${WORK_FOLDER:-$HOME/promgr/work}"
DEFAULT_EDITOR="${DEFAULT_EDITOR:-$TERMI $EDITOR}"
mkdir -p "$TPL_FOLDER" || exit 1
mkdir -p "$WORK_FOLDER" || exit 1

TPL_FOLDER=$(realpath $TPL_FOLDER)
WORK_FOLDER=$(realpath $WORK_FOLDER)

if [ -f "$HOME/.config/promgr.toml" ]; then
  echo Warning: the old promgr config saved as $HOME/.config/promgr.toml.bak
  mv "$HOME/.config/promgr.toml" "$HOME/.config/promgr.toml.bak"
fi

cat > "$HOME/.config/promgr.toml" << EOF
[paths]
templates = "$TPL_FOLDER"
work = "$WORK_FOLDER"

[apps]
editor = "$DEFAULT_EDITOR"
EOF

CURRENT_FOLDER="$(realpath $(dirname $0))"
if [ ! -f "$TPL_FOLDER/template" ]; then
  ln -sf "$CURRENT_FOLDER/default_template" "$TPL_FOLDER/template"
fi

echo Promgr is fully set up. Restart ulauncher to start using it.
