def capitalize_str(old_str):
    if old_str:
        return "%s%s" % (old_str[0].upper(), old_str[1:])
    else:
        return old_str
