#!/usr/bin/python3.8
# Main script for azalea_libcxx_builder
#
# This scripts builds kernel and user-mode versions of libcxx that are customised for use with Project Azalea. It also
# builds libunwind for use within the kernel.
#
# Requires python3.8 or newer.

from contextlib import contextmanager
import os
import configparser
import argparse
import shutil

def main(config):
  if not os.path.exists("output/kernel_lib"):
    os.makedirs("output/kernel_lib", exist_ok=True)

  cxxflags = [
    "-fno-threadsafe-statics",
    "-nostdinc++",
    "-mcmodel=large",
    "-isystem %s" % os.path.abspath("threading_adapter/cxx_include"),
    "-isystem %s" % os.path.abspath(os.path.join(config["PATHS"]["libcxx_base"], "src")),
    "-isystem %s" % os.path.abspath(os.path.join(config["PATHS"]["libcxx_base"], "include")),
    "-isystem %s" % os.path.abspath(os.path.join(config["PATHS"]["kernel_base"], "kernel"))
    ]

  cxx_install_path = os.path.abspath(os.path.join(config["PATHS"]["sys_image_root"], "apps", "developer", "libcxx-kernel"))
  unwind_install_path = os.path.abspath(os.path.join(config["PATHS"]["sys_image_root"], "apps", "developer", "libunwind-kernel"))
  libcxxabi_install_path = os.path.abspath(os.path.join(config["PATHS"]["sys_image_root"], "apps", "developer", "libcxxabi-kernel"))

  os.environ["CXXFLAGS"] = " ".join(cxxflags)
  os.environ["CFLAGS"] = os.environ["CXXFLAGS"]

  cmake_libcxx_flags = [
    "cmake",
    os.path.join("..", "..", config["PATHS"]["libcxx_base"]),
    "-DLLVM_PATH=%s" % config["PATHS"]["llvm_base"],
    "-DCMAKE_INSTALL_PREFIX=%s" % cxx_install_path,
    "-DLIBCXX_ENABLE_EXCEPTIONS=OFF",
    "-DLIBCXX_ENABLE_SHARED=OFF",
    "-DLIBCXX_ENABLE_STDIN=OFF",
    "-DLIBCXX_ENABLE_STDOUT=OFF",
    "-DLIBCXX_HAS_EXTERNAL_THREAD_API=ON",
    "-DLIBCXX_HAS_PTHREAD_API=OFF",
    "-DLIBCXX_CXX_ABI=libcxxabi",
    "-DCMAKE_CXX_COMPILER=/usr/bin/clang++",
    "-DCMAKE_C_COMPILER=/usr/bin/clang",
    "-DLIBCXX_CXX_ABI_INCLUDE_PATHS=%s" % os.path.join("..", "..", config["PATHS"]["libcxxabi_base"], "include"),
    ]

  cmake_libunwind_flags = [
    "cmake",
    os.path.join("..", "..", config["PATHS"]["libunwind_base"]),
    "-DLLVM_PATH=%s" % config["PATHS"]["llvm_base"],
    "-DCMAKE_INSTALL_PREFIX=%s" % unwind_install_path,
    "-DLIBUNWIND_ENABLE_SHARED=OFF",
    "-DLIBUNWIND_ENABLE_STATIC=ON",
    "-DCMAKE_CXX_COMPILER=/usr/bin/clang++",
    "-DCMAKE_C_COMPILER=/usr/bin/clang",
    "-DLLVM_ENABLE_LIBCXX=ON",
    "-DLIBUNWIND_ENABLE_ASSERTIONS=OFF",
    "-DCMAKE_BUILD_TYPE=RELEASE",
    "-DLIBUNWIND_ENABLE_THREADS=OFF",
    #"-DLIBUNWIND_C_FLAGS=%s" % ";".join(cxxflags)
  ]

  cmake_libcxxabi_flags = [
    "cmake",
    os.path.join("..", "..", config["PATHS"]["libcxxabi_base"]),
    "-DLLVM_PATH=%s" % config["PATHS"]["llvm_base"],
    "-DCMAKE_INSTALL_PREFIX=%s" % libcxxabi_install_path,
    "-DCMAKE_CXX_COMPILER=/usr/bin/clang++",
    "-DCMAKE_C_COMPILER=/usr/bin/clang",
    "-DLIBCXXABI_ENABLE_ASSERTIONS=OFF",
    "-DCMAKE_BUILD_TYPE=RELEASE",
    "-DLIBCXXABI_HAS_EXTERNAL_THREAD_API=ON",
    "-DLIBCXXABI_ENABLE_NEW_DELETE_DEFINITIONS=OFF",
    "-DLIBCXXABI_ENABLE_SHARED=OFF",
    "-DLIBCXXABI_ENABLE_STATIC=ON",
    "-DLIBCXXABI_BAREMETAL=ON",
    "-DLIBCXXABI_ENABLE_STATIC_UNWINDER=ON",
    "-DLIBCXXABI_ENABLE_PIC=OFF",
    "-DLIBCXXABI_LIBCXX_INCLUDE_DIRS=%s" % os.path.join("..", "..", config["PATHS"]["libcxxabi_base"], "include"),
  ]

  os.makedirs("output/kernel_lib", exist_ok = True)
  os.makedirs("output/kernel_libunwind", exist_ok = True)
  os.makedirs("output/kernel_libcxxabi", exist_ok = True)

  print ("--- BUILD LIBCXXABI ---")

  cxxflags = cxxflags + [
    "-D _LIBUNWIND_IS_BAREMETAL",]
  os.environ["CXXFLAGS"] = " ".join(cxxflags)
  os.environ["CFLAGS"] = os.environ["CXXFLAGS"]

  with cd("output/kernel_libcxxabi"):
    os.system(" ".join(cmake_libcxxabi_flags))
    os.system("make")
    os.system("make install")

  os.system("scons sys_image_root='%s' kernel_base='%s'" % (config["PATHS"]["sys_image_root"], os.path.join(config["PATHS"]["kernel_base"])))
  os.system("scons install")

  print ("")
  print ("--- BUILD LIBUNWIND ---")

  cxxflags = cxxflags + [
    "-D _LIBUNWIND_IS_BAREMETAL",]
  os.environ["CXXFLAGS"] = " ".join(cxxflags)
  os.environ["CFLAGS"] = os.environ["CXXFLAGS"]

  with cd("output/kernel_libunwind"):
    os.system(" ".join(cmake_libunwind_flags))
    os.system("make")
    os.system("make install")

    # For some reason this doesn't install the headers, so copy them manually
    os.makedirs(os.path.join(unwind_install_path, "include"), exist_ok = True)
    shutil.copytree(os.path.join("..", "..", config["PATHS"]["libunwind_base"], "include"),
                    os.path.join(unwind_install_path, "include"),
                    dirs_exist_ok = True)

  print ("")
  print ("--- BUILD LIBCXX ---")
  with cd("output/kernel_lib"):
    os.system(" ".join(cmake_libcxx_flags))
    os.system("make")
    os.system("make install")

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
  populate_field(paths, args_dict, "libunwind_base", "LLVM Libunwind base directory")
  populate_field(paths, args_dict, "libcxxabi_base", "LLVM Libcxxabi base directory")
  populate_field(paths, args_dict, "sys_image_root", "Azalea system image root directory")
  populate_field(paths, args_dict, "llvm_base", "LLVM project llvm source folder")

def populate_field(config_section, args_dict, cfg_name, human_name):
  if (cfg_name in args_dict) and args_dict[cfg_name]:
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
    argp.add_argument("--libcxxabi_base", type = str, help = "Location of LLVM Libcxxabi source code tree")
    argp.add_argument("--libunwind_base", type = str, help = "Location of LLVM Libunwind source code tree")
    argp.add_argument("--sys_image_root", type = str, help = "Root of the Azalea system image's filesystem")
    argp.add_argument("--config_file", type = str, default = "config/saved_config.ini", help = "Config file location")
    argp.add_argument("--llvm_base", type = str, help = "Location of llvm-project's llvm folder")
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