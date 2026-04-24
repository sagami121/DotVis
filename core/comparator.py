def compare_configs(config_a, config_b):
    added = {k: config_b[k] for k in config_b if k not in config_a}
    removed = {k: config_a[k] for k in config_a if k not in config_b}
    modified = {k: (config_a[k], config_b[k]) for k in config_a if k in config_b and config_a[k] != config_b[k]}

    return {'added': added, 'removed': removed, 'modified': modified}
