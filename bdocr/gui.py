import webview
from threading import Thread
from app import app
import requests

def start_server():
    app.run(host='127.0.0.1', port=5000)

def close_server():
    requests.post('http://127.0.0.1:5000/shutdown')

if __name__ == '__main__':
    t = Thread(target=start_server)
    t.start()

    try:
        window = webview.create_window("Patient Record Management System", 
                                       "http://127.0.0.1:5000", 
                                       resizable=False,
                                       height=800,
                                       width=1200
                                      )
        webview.start()
    except KeyboardInterrupt:
        close_server()
    finally:
        close_server()
