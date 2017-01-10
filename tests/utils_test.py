import time


def ptime():
    now = time.time()
    while True:
        time.sleep(1)
        if time.time() - now > 5:
            print("5 secs time out")
            print(time.time())
            print(now)
            break


ptime()
