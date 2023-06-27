from flask import Flask, redirect, url_for, abort, render_template
from turbo_flask import Turbo
from classes import Video
import asyncio
import aiohttp
import threading
from killable_thread import KillableThread
import signal, sys, os
import uuid

app = Flask(__name__)
app.config['SERVER_NAME'] = '127.0.0.1:5000'
turbo = Turbo(app)

videos = []
events = []
httpSession = None
pid = None
lock = asyncio.Lock()

def get_video_by_id(id):
    video = [video for video in videos if video.id == id]
    if len(video) == 0:
        abort(404)
    return video[0]

@app.route('/', methods=['GET'])
def index():
    return render_template('/index.html', videos=videos)

@app.route('/delete/<id>', methods=['POST'])
def delete(id):
    video = get_video_by_id(id)
    videos.remove(video)
    if turbo.can_stream():
        return turbo.stream(
            turbo.remove(f'video-{video.id}'))

async def create_video(link: str):
    global videos, events, httpSession, lock
    
    await lock.acquire()
    videos.append(Video())
    video_id = videos[-1].id
    asyncio.create_task(videos[-1].create(link, httpSession))
    lock.release()
    
    events.append(('create_video', video_id, uuid.uuid4().hex))

async def creation_check(event):
    id = event[1]
    video = get_video_by_id(id)
    if video.data == None:
        return False
    
    with app.app_context():
        if turbo.can_push():
            turbo.push(turbo.replace(render_template('_video.html', video=video), f'video-{video.id}'))
    
    return True

event_types = {
    'create_video': creation_check
}

async def main():
    global videos, httpSession, pid, events
    pid = os.getpid()
    httpSession = aiohttp.ClientSession()
    await create_video('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

    while True:
        for e in events:
            if await event_types[e[0]](e):
                events.remove(e)
        await asyncio.sleep(.2)

def main_wrapper():
    asyncio.run(main())
    
def interrupt_handler(a, b):
    global th
    th.raiseExc(KeyboardInterrupt)
    sys.exit(0)

if __name__ == "__main__":
    th = KillableThread(target=main_wrapper)
    signal.signal(signal.SIGINT, interrupt_handler)
    th.start()
    app.run(debug=False)
    th.join()
    