def ajax_exception(err) :
    msg = str(err) or repr(err)
    code = 500
    m = re.compile(r'(\d+)\s+(.+)$').match(msg)
    if m:
        code = int(m.group(1))
        msg = m.group(2)
    logging.exception("Error %r, <%s>", err, err)
    return msg, code
