#!/usr/bin/python3
# Main script for azalea_libcxx_builder
#
# This scripts builds kernel and user-mode versions of libcxx that are customised for use with Project Azalea.

from contextlib import contextmanager
import os
import configparser
import argparse

def main(config):
  if not os.path.exists("output/kernel_lib"):
    os.mkdir("output/kernel_lib")

  cxxflags = [
    "-fno-threadsafe-statics",
    "-isystem %s" % os.path.abspath("threading_adapter/cxx_include"),
    "-isystem %s" % os.path.abspath(os.path.join(config["PATHS"]["libcxx_base"], "src")),
    "-isystem %s" % os.path.abspath(os.path.join(config["PATHS"]["kernel_base"], "kernel")),
    "-isystem %s" % os.path.abspath(os.path.join(config["PATHS"]["kernel_base"], "external", "libcxxrt-master", "src")),
    ]

  install_path = os.path.abspath(os.path.join(config["PATHS"]["sys_image_root"], "apps", "developer", "libcxx-kernel"))

  os.environ["CXXFLAGS"] = " ".join(cxxflags)

  cmake_flags = [
    "cmake",
    os.path.join("..", "..", config["PATHS"]["libcxx_base"]),
    "-DLLVM_CONFIG_PATH=/usr/lib/llvm-6.0/bin/llvm-config",
    "-DCMAKE_INSTALL_PREFIX=%s" % install_path,
    "-DLIBCXX_ENABLE_EXCEPTIONS=OFF",
    "-DLIBCXX_ENABLE_SHARED=OFF",
    "-DLIBCXX_ENABLE_STDIN=OFF",
    "-DLIBCXX_ENABLE_STDOUT=OFF",
    "-DLIBCXX_HAS_EXTERNAL_THREAD_API=ON",
    "-DLIBCXX_HAS_PTHREAD_API=OFF",
    "-DLIBCXX_CXX_ABI=libcxxrt",
    "-DCMAKE_CXX_COMPILER=/usr/bin/clang++",
    "-DCMAKE_C_COMPILER=/usr/bin/clang",
    ]

  with cd("output/kernel_lib"):
    os.system(" ".join(cmake_flags))
    os.system("make")
    os.system("make install")

  os.system("scons sys_image_root='%s' kernel_base='%s'" % (config["PATHS"]["sys_image_root"], os.path.join(config["PATHS"]["kernel_base"])))
  os.system("scons install")

# An easy way to wrap CD calls so they get reverted upon exiting or exceptions.
#
# Cheekily taken from this Stack Overflow answer:
# https://stackoverflow.com/questions/431684/how-do-i-change-directory-cd-in-python/24176022#24176022
@contextmanager
def cd(newdir):
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)


def regenerate_config(config, cmd_line_args):
  args_dict = vars(cmd_line_args)

  if "PATHS" not in cfg.sections():
    cfg["PATHS"] = { }

  paths = config["PATHS"]

  populate_field(paths, args_dict, "kernel_base", "Kernel source base directory")
  populate_field(paths, args_dict, "libcxx_base", "LLVM Libc++ base directory")
  populate_field(paths, args_dict, "sys_image_root", "Azalea system image root directory")

def populate_field(config_section, args_dict, cfg_name, human_name):
  if args_dict[cfg_name]:
    config_section[cfg_name] = args_dict[cfg_name]
  if cfg_name not in config_section:
    config_section[cfg_name] = prompt_for_value(human_name)

def prompt_for_value(field_name):
  prompt_str = "Enter the following: " + field_name + "\n"
  return input(prompt_str)

if __name__ == "__main__":
  try:
    argp = argparse.ArgumentParser(description = "Project Azalea Builder helper")
    argp.add_argument("--kernel_base", type = str, help = "Location of the base of the Azalea kernel source code tree")
    argp.add_argument("--libcxx_base", type = str, help = "Location of LLVM Libc++ source code tree")
    argp.add_argument("--sys_image_root", type = str, help = "Root of the Azalea system image's filesystem")
    argp.add_argument("--config_file", type = str, default = "config/saved_config.ini", help = "Config file location")
    args = argp.parse_args()

    flags = "r" if os.path.exists(args.config_file) else "a+"
    cfg_file = open(args.config_file, flags)
    cfg = configparser.ConfigParser()
    cfg.read_file(cfg_file)
    cfg_file.close()

    regenerate_config(cfg, args)
    main(cfg)

    cfg_file = open(args.config_file, "w")
    cfg.write(cfg_file)
    cfg_file.close()

  except KeyboardInterrupt:
    print ("Build interrupted")