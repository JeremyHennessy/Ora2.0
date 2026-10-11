"""Typed ordinary task readiness; never a learning evaluator."""
def endpoint(metrics,minimum):
    keys=('post_food','fresh_attempts','ticks')
    return (type(metrics) is dict and metrics.get('verified') is True
            and type(minimum) is int and 0<=minimum<=16
            and all(type(metrics.get(k)) is int for k in keys)
            and metrics['fresh_attempts']==16 and metrics['ticks']>=272
            and minimum<=metrics['post_food']<=16)
