#coding=utf8
from datetime import datetime, date
from pyutil import str_to_unicode

def shorten(name, limit):
    '''
    >>> shorten('12345', 2)
    '1..5'
    '''
    if not limit or not isinstance(name, basestring):
        return name
    if len(name) <= limit:
        return name
    half = max(1, limit - 6, int(limit / 2) - 1)
    half1 = max(1, limit - 2 - half)
    return name[:half] + '..' + name[-half1:]

def pformat(d, max_v_limit=0):
    u'''
    >>> pformat(dict(a=1, b='abcd'))
    u'{a=1, b=abcd}'
    >>> pformat(['a', 'b', 1])
    u'[a, b, 1]'
    >>> pformat(dict(a=1, b='abcdefg'), max_v_limit=5)
    u'{a=1, b=a..fg}'
    >>> pformat(1)
    u'1'
    >>> pformat([1,2,3], 2)
    u'[1, 2]'
    >>> class C: pass
    >>> o = C()
    >>> o.a = 12345
    >>> pformat(o, max_v_limit=2)
    u'C({a=1..5})'
    '''
    if isinstance(d, (list, tuple)):
        if max_v_limit:
            d = d[:max_v_limit]
        braces = '()' if isinstance(d, tuple) else '[]'
        return u''.join([braces[0],
            u', '.join(pformat(x, max_v_limit=max_v_limit) for x in d),
            braces[1],
            ])
    elif isinstance(d, dict):
        return '{%s}' % u', '.join('%s=%s' % (k, pformat(v, max_v_limit=max_v_limit)) for k, v in d.iteritems())
    elif isinstance(d, (date, datetime)):
        return fmt_datetime(d)
    elif hasattr(d, '__dict__'):
        return u'%s(%s)' % (d.__class__.__name__, pformat(d.__dict__, max_v_limit=max_v_limit))
    else:
        my_shorten = lambda x: (shorten(x, limit=max_v_limit) if max_v_limit else x)
        try:
            s = u'%s' % str_to_unicode(d, strict=False)
        except:
            s = u'%r' % d
        return my_shorten(s)

def fmt_exception(e):
    try:
        m = str(e).decode('utf8')
    except:
        m = unicode(e)
    return '%s(%s)' % (e.__class__.__name__, m)

def fmt_datetime(t, fmt=None, default=None):
    from datetime import datetime
    if not t:
        return default
    fmt_ = fmt or ('%Y-%m-%d %H:%M:%S' if isinstance(t, datetime) else '%Y-%m-%d')
    return t.strftime(fmt_)

def pformat_duration(seconds, en_name=False):
    u'''
    >>> pformat_duration(.1) == u'0.1秒'
    True
    >>> pformat_duration(30.1) == u'30秒'
    True
    >>> pformat_duration(90) == u'1.5分钟'
    True
    >>> pformat_duration(125) == u'2分钟'
    True
    >>> pformat_duration(125, en_name=True)
    u'2m'
    >>> pformat_duration(7200.1) == u'2小时'
    True
    >>> pformat_duration(7200.1, en_name=True)
    u'2h'
    >>> pformat_duration(3600 * 36, en_name=True)
    u'1.5d'
    '''
    sign = '' if seconds >= 0 else '-'
    seconds = abs(seconds)
    if seconds < 60:
        unit = 's'
    elif seconds < 3600:
        unit = 'm'
    elif seconds < 3600 * 24:
        unit = 'h'
    else:
        unit = 'd'

    factor = dict(s=1, m=60, h=3600, d=3600*24)[unit]
    v = float(seconds) / factor
    if seconds == factor * int(v):
        dur = '%s' % int(v)
    elif v < 2:
        dur = '%.1f' % v
    else:
        dur = '%s' % int(v)

    if not en_name:
        unit = dict(s=u'秒', m=u'分钟', h=u'小时', d=u'天')[unit]
    return u'%s%s%s' % (sign, dur, unit)

def pformat_timedelta(delta):
    return pformat_duration(delta.total_seconds())
