import threading
import ctypes
import inspect
import asyncio
import time

def _async_raise(tid, exctype):
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    
    if res == 0:
        raise ValueError("invalid thread id")
    
    if res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

class KillableThread(threading.Thread):
    def _get_my_tid(self):
        if not self.is_alive():
            raise threading.ThreadError("the thread is not active")
        
        if hasattr(self, "_thread_id"):
            return self._thread_id
        
        for tid, tobj in threading._active.items():
            if tobj is self:
                self._thread_id = tid
                return tid
        
        raise AssertionError("couldn't find thread id")
    
    def raiseExc(self, exctype):
        _async_raise(self._get_my_tid(), exctype)
    
if __name__ == '__main__':
    async def task():
        while True:
            await asyncio.sleep(1)
    
    async def main():
        await asyncio.gather(task())
    
    def main_wrapper():
        asyncio.run(main())
    
    th = KillableThread(main_wrapper())
    try:
        th.start()
    except (KeyboardInterrupt, SystemExit) as e:
        print('Catched')
        th.raiseExc(e)
        while th.is_alive():
            time.sleep(.1)
            th.raiseExc(e)
            