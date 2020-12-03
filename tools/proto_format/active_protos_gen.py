#!/usr/bin/env python3

# Generate ./api/versioning/BUILD based on packages with files containing
# "package_version_status = ACTIVE."

import os
import string
import subprocess
import sys

BUILD_FILE_TEMPLATE = string.Template(
    """# DO NOT EDIT. This file is generated by tools/proto_format/active_protos_gen.py.

licenses(["notice"])  # Apache 2

load("@rules_proto//proto:defs.bzl", "proto_library")

# This tracks active development versions of protos.
proto_library(
    name = "active_protos",
    visibility = ["//visibility:public"],
    deps = [
$active_pkgs    ],
)

# This tracks frozen versions of protos.
proto_library(
    name = "frozen_protos",
    visibility = ["//visibility:public"],
    deps = [
$frozen_pkgs    ],
)
""")


# Key sort function to achieve consistent results with buildifier.
def BuildOrderKey(key):
  return key.replace(':', '!')


def DepsFormat(pkgs):
  if not pkgs:
    return ''
  return '\n'.join(
      '        "//%s:pkg",' % p.replace('.', '/') for p in sorted(pkgs, key=BuildOrderKey)) + '\n'


# Find packages with a given package version status in a given API tree root.
def FindPkgs(package_version_status, api_root):
  try:
    active_files = subprocess.check_output(
        ['grep', '-l', '-r',
         'package_version_status = %s;' % package_version_status,
         api_root]).decode().strip().split('\n')
    api_protos = [f for f in active_files if f.endswith('.proto')]
  except subprocess.CalledProcessError:
    api_protos = []
  return set([os.path.dirname(p)[len(api_root) + 1:] for p in api_protos])


if __name__ == '__main__':
  api_root = sys.argv[1]
  active_pkgs = FindPkgs('ACTIVE', api_root)
  frozen_pkgs = FindPkgs('FROZEN', api_root)
  sys.stdout.write(
      BUILD_FILE_TEMPLATE.substitute(active_pkgs=DepsFormat(active_pkgs),
                                     frozen_pkgs=DepsFormat(frozen_pkgs)))