def schedule_at_loop(loop, future, callback=None):
    if callable(future):
        future = future()
    loop.add_future(future, callback)
