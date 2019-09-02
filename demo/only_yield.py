import socket
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE

selector = DefaultSelector()
stopped = False
urls_todo = {"/", "/1", "/2"}


class Future:
    def __init__(self):
        self.result = None
        self._callbacks = []

    def add_done_callback(self, fn):
        self._callbacks.append(fn)

    def set_result(self, result):
        self.result = result
        for fn in self._callbacks:
            fn(self)


class Crawler:
    def __init__(self, url):
        self.url = url
        self.response = b""

    def fetch(self):
        sock = socket.socket()
        sock.setblocking(False)
        try:
            sock.connect(('xkcd.com', 80))
        except BlockingIOError:
            pass

        f = Future()

        def on_connected():
            f.set_result(None)

        selector.register(sock.fileno(), EVENT_WRITE, on_connected)
        yield f
        selector.unregister(sock.fileno())
        get = "GET {0} HTTP/1.0\r\nHost:xkcd.com\r\n\r\n".format(self.url)
        sock.send(get.encode('ascii'))

        global stopped
        while True:
            f = Future()

            def on_readable():
                """
                此处有个关键点需要理解：
                过程执行中，遇到io操作，先通过register注册一个回调，然后把io事件委托给操作系统，
                由于接下来的代码运行依赖io操作的结果，所以让出CPU控制权，等操作系统把事情办妥后，
                通过回调函数，把结果返回原来暂停的地方以便继续之前暂停的代码，这样，协程的作用就
                很清晰了，future的含义也明朗了
                """
                f.set_result(sock.recv(4096))

            """CPU不一定一次全部接收完成，每次接收到数据时都会产生可读事件，所以这里循环读"""
            selector.register(sock.fileno(), EVENT_READ, on_readable)
            chunk = yield f
            selector.unregister(sock.fileno())
            if chunk:
                self.response += chunk
            else:
                print(self.response)
                urls_todo.remove(self.url)
                if not urls_todo:
                    stopped = True
                break


class Task:
    def __init__(self, coro):
        self.coro = coro
        f = Future()
        f.set_result(None)  # 这里必须是None，因为用send来激活生成器，只能传入None。用next()也行
        self.step(f)  # 激活生成器

    def step(self, future):
        try:
            next_future = self.coro.send(future.result)  # 主要作用就是给程序返回操作系统完成io操作后的结果
        except StopIteration:
            return

        next_future.add_done_callback(self.step)


def loop():
    """
    windows中DefaultSelector选择的是select（Linux中自动选择epoll）
    如果此处不使用stopped来控制循环，当最后一个注册事件被处理完成，
    如果再次循环，则会报错（即select没东西可等待了），而epoll不会存在
    这个问题，所以这个stopped是个关键点。
    """
    while not stopped:
        events = selector.select()
        for event_key, event_mask in events:
            callback = event_key.data
            callback()


if __name__ == "__main__":
    import time
    start = time.time()
    for url in urls_todo:
        crawler = Crawler(url)
        Task(crawler.fetch())
    loop()
    print(time.time() - start)


































