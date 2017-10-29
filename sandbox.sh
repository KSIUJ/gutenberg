#!/bin/sh

dir="$1"
shift
bwrap --ro-bind / / \
      --tmpfs /home \
      --tmpfs /run \
      --tmpfs /tmp \
      --bind "$dir" "$dir" \
      --proc /proc \
      --dev /dev \
      --chdir / \
      --unshare-pid \
      --unshare-net \
      "$@"
