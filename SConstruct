import os
import platform

import config

def main_build_script(cfg_env):
  env = build_default_env()
  developer_path = os.path.abspath(os.path.join(cfg_env["sys_image_root"], "apps", "developer"))
  env.AppendENVPath('CPATH', os.path.join(developer_path, "libcxx-kernel", "include", "c++", "v1"))
  env.AppendENVPath('CPATH', os.path.join(developer_path, "libc", "include"))
  env.AppendENVPath('CPATH', os.path.join(developer_path, "kernel", "include"))
  env.AppendENVPath('CPATH', os.path.abspath(os.path.join(cfg_env["kernel_base"], "kernel")))
  env['CXXFLAGS'] = '-Wall -fno-pic -nostdinc++ -nostdinc -nostdlib -nodefaultlibs -mcmodel=large -ffreestanding -fno-exceptions -ffunction-sections -std=c++17 -U _LINUX -U __linux__ -D __AZALEA__ -D _LIBCPP_BUILDING_LIBRARY'

  lib_obj = env.SConscript("threading_adapter/SConscript", 'env', variant_dir='output', duplicate=0)
  install_folder = os.path.join(developer_path, "libcxx-kernel", "lib")
  env.Install(install_folder, lib_obj)
  thread_header = env.File("threading_adapter/cxx_include/__external_threading")
  header_folder = os.path.join(developer_path, "libcxx-kernel", "include", "c++", "v1")
  env.Install(header_folder, thread_header)
  Alias('install', install_folder)
  Alias('install', header_folder)

def copy_environ_param(name, env_dict):
  if name in os.environ:
    env_dict[name] = os.environ[name]

def build_default_env():
  env_to_copy_in = { }
  copy_environ_param('PATH', env_to_copy_in)
  copy_environ_param('CPATH', env_to_copy_in)
  copy_environ_param('TEMP', env_to_copy_in)
  copy_environ_param('TMP', env_to_copy_in)
  copy_environ_param('INCLUDE', env_to_copy_in)
  copy_environ_param('LIB', env_to_copy_in)

  env = Environment(ENV = env_to_copy_in, tools=['default', 'nasm'])
  env['CPPPATH'] = '#'
  env['AS'] = 'nasm'
  env['RANLIBCOM'] = ''
  env['ASCOMSTR'] =   "Assembling:   $TARGET"
  env['CCCOMSTR'] =   "Compiling:    $TARGET"
  env['CXXCOMSTR'] =  "Compiling:    $TARGET"
  env['LINKCOMSTR'] = "Linking:      $TARGET"
  env['ARCOMSTR'] =   "(pre-linking) $TARGET"
  env['LIBS'] = [ ]

  return env

def construct_variables():
  var = Variables(["config/default_config.py", "variables.cache" ], ARGUMENTS)
  var.AddVariables(
    PathVariable("sys_image_root",
                 "Root of Azalea system image. Look for include files, libraries and installation locations here.",
                 None,
                 PathVariable.PathIsDir),
    PathVariable("kernel_base",
                 "Root of the Azalea kernel source code.",
                 None,
                 PathVariable.PathIsDir))

  e = Environment(variables = var)

  var.Save("variables.cache", e)

  return e

config = construct_variables()
main_build_script(config)