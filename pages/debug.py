

def debug_(*kargs, **kwargs):
    """
    Print stuff if settings.DEBUG is true. 
    Accpets a tuple of elements, or a single one. (like 'print')
    Optional kwargs:
     * stack: prints a complete stacktrace
     * label: prints an extra label (to e.g. flag a location)

    In [2]: _debug_(123,123,123)
    ...<ipython console>:1  123 123 123
    In [3]: _debug_(123)
    ...<ipython console>:1  123
    In [4]: _debug_('asdasd')
    ...<ipython console>:1  asdasd
    In [5]: _debug_('asdasd','asdasd','asdasdasd','asdasd')
    ...<ipython console>:1  asdasd asdasd asdasdasd asdasd
    """
    import logging, traceback
    msg = ''
    if kwargs.get('stack', False):
        for ctx in  traceback.extract_stack()[-6:-1]:
            msg += "s:%d (%s)\n" % ('/'.join(ctx[0].split('/')[-3:]),ctx[1],ctx[2])

    else:
        stack=traceback.extract_stack()[-2]
        msg += "%s:%d (%s)\t" % ('/'.join(stack[0].split('/')[-3:]),stack[1],stack[2])

    if kwargs.get('label',False):
        msg=msg+' '+kwargs.get('label',False)

    logger = kwargs.get('logger', logging.debug)
    
    for k in kargs:
        msg = msg + ' ' + str(k)
        if hasattr(k,'message') and hasattr(k,'args'):
            logger = logging.error

    kwargs.get('logger', logger)(msg)
    
def break_here():
    try:
        import ipdb as pdb
    except ImportError:
        import pdb; 
    pdb.set_trace()
