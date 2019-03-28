/// @file
/// @brief Implements an external threading library that allows libcxx to be used inside the Azalea kernel.

#include <__config>
#include <chrono>
#include <errno.h>
#include "cxx_include/__external_threading"
#include "processor/processor.h"

_LIBCPP_BEGIN_NAMESPACE_STD

int __libcpp_mutex_lock(__libcpp_mutex_t *__m)
{
  if (__m != nullptr)
  {
    return static_cast<int>(klib_synch_mutex_acquire(*__m, MUTEX_MAX_WAIT));
  }
  else
  {
    return -1;
  }
}

bool __libcpp_mutex_trylock(__libcpp_mutex_t *__m)
{
  if (__m != nullptr)
  {
    SYNC_ACQ_RESULT res;
    res = klib_synch_mutex_acquire(*__m, 0);

    if (res == SYNC_ACQ_ACQUIRED)
    {
      return true;
    }
    else
    {
      return false;
    }
  }
  else
  {
    return false;
  }
}

int __libcpp_mutex_unlock(__libcpp_mutex_t *__m)
{
  if (__m != nullptr)
  {
    klib_synch_mutex_release(*__m, false);
    return 0;
  }
  else
  {
    return -1;
  }
}

void __libcpp_thread_yield()
{
  task_yield();
}

_LIBCPP_END_NAMESPACE_STD