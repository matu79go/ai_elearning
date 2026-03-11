from flask import Blueprint, g


def dual_route(bp, rule, **kwargs):
    """Register both /path and /ja/path on a blueprint"""
    def decorator(f):
        bp.add_url_rule(rule, f.__name__, f, **kwargs)
        bp.add_url_rule('/ja' + rule, f.__name__ + '_ja', f, **kwargs)
        return f
    return decorator
