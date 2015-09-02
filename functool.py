#coding=utf8

import functools, time, sys, logging
from fmtutil import fmt_exception

def throttle(wait, exception_wait=0):
    u"""
    在指定时间间隔内, 只调用一次的decorator. 如果在时间间隔内第二次调用, 则返回上一次调用的结果.
    可作用于任何函数和方法.

    See http://underscorejs.org/#throttle

    wait - in ms. 两次调用的间隔时间
    exception_wait - in ms. 发生异常时下次调用的间隔. 0表示下次调用无需间隔

    >>> @throttle(wait=1000) # load_urls 1秒内只会被调用一次
    ... def load_urls():
    ...   print 'loaded'
    ...   return 'ok'
    >>> load_urls() # 第一次调用执行
    loaded
    'ok'
    >>> load_urls() # 1秒内第二次调用, 不执行, 直接返回上次调用的结果
    'ok'
    >>> time.sleep(1)
    >>> load_urls() # 1秒之后再调用, 执行
    loaded
    'ok'
    """

    wait = wait / 1000.0
    exception_wait = exception_wait / 1000.0

    ns = dict(
            cache_at = None, # 计算开始的时间 (非计算完成时间, 以减少多线程环境下计算被重复进行的概率)
            )

    def wrapper(f):
        @functools.wraps(f)
        def throttled(*args, **kwargs):
            cache_at = ns['cache_at']
            if cache_at and time.time() - cache_at < wait:
                while True: # 获取计算结果并返回
                    if 'cached_value' in ns:
                        return ns['cached_value']
                    time.sleep(.1)

            ns['cache_at'] = time.time()
            try:
                ns['cached_value'] = f(*args, **kwargs)
            except:
                if 'cached_value' not in ns:
                    ns['cached_value'] = None # 赋值以避免其他线程的计算一直等待结果
                ns['cached_at'] = time.time() - wait + exception_wait
                raise
            return ns['cached_value']
        return throttled

    return wrapper


def retries(max_tries, delay=1, backoff=2, exceptions=(Exception,), ignore_exceptions=None, hook=None):
    """Function decorator implementing retrying logic.

    delay: Sleep this many seconds * backoff^try number after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    ignore_exceptions: A tuple of exception classes to not catch; default None
    hook: A function with the signature myhook(tries_remaining, exception);
          default None

    The decorator will call the function up to max_tries times if it raises
    an exception.

    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.

    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """

    def default_hook(func, tries_remaining, exception, delay):
        """
        tries_remaining: The number of tries remaining.
        exception: The exception instance which was raised.
        """
        # 首次也抛异常，方便调试时追查问题
        log = logging.exception if tries_remaining == max_tries - 1 else logging.warn
        log("%s: Caught '%s: %s', %d tries remaining, sleeping for %s seconds",
                func.__name__, type(exception).__name__, exception, tries_remaining, delay)

    hook = hook or default_hook

    def dec(func):
        @functools.wraps(func)
        def f2(*args, **kwargs):
            mydelay = delay
            tries = range(max_tries)
            tries.reverse()
            for tries_remaining in tries:
                try:
                   return func(*args, **kwargs)
                except exceptions as e:
                    if ignore_exceptions and isinstance(e, ignore_exceptions):
                        raise
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(func, tries_remaining, e, mydelay)
                        time.sleep(mydelay)
                        mydelay = mydelay * backoff
                    else:
                        raise
                else:
                    break
        return f2
    return dec

def catch_exception(hook=None, exceptions=(Exception,), log_exception=True, log_prefix=''):
    """
    The decorator will catch the exception and return the result of hook(exception).

    hook: A function with the signature myhook(exception);
          default None (just re raise the exception)
    exceptions: A tuple of exception classes; default (Exception,)
    log_exception: whether to logging the exception
    log_prefix: logging prefix

    by default, just logging and re raise the exception
    """

    def try_except(func):
        @functools.wraps(func)
        def f2(*args, **kwargs):
            try:
               return func(*args, **kwargs)
            except exceptions as e:
                if log_exception:
                    import logging
                    logging.exception('%s%s', log_prefix, fmt_exception(e))
                if hook:
                    return hook(e)
                else:
                    raise
        return f2
    return try_except

def keep_run(delay):
    """
    The decorator will catch the exception, delay a while, and rerun.
    Used for thread run

    delay: when exception, delay given seconds, and then rerun
    """

    import time
    def wrapper(func):
        @functools.wraps(func)
        def f2(*args, **kwargs):
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.exception(fmt_exception(e))
                    if delay:
                        time.sleep(delay)
        return f2
    return wrapper
