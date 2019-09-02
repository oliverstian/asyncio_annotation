"""
协程编码模式的三个要点：事件循环（心脏） + 回调（驱动生成器） + epoll（io多路复用，Windows是select）
"""
import asyncio
import time


async def get_html(url):
    print("start get url")
    await asyncio.sleep(3)
    await asyncio.sleep(3)
    print("end get url")

if __name__ == "__main__":
    start_time = time.time()
    loop = asyncio.get_event_loop()

    cora = get_html("http://www.baidu.com")
    task = loop.create_task(cora)
    loop.run_until_complete(task)

    # tasks = [get_html("http://www.baidu.com") for i in range(10)]
    # loop.run_until_complete(asyncio.wait(tasks))
    print(time.time() - start_time)




















