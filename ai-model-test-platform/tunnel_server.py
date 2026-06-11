from flask import Flask, request, Response
import requests

app = Flask(__name__)

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
def catch_all(path):
    if path.startswith('api/'):
        return proxy_request(BACKEND_URL, '/' + path)
    if path == 'ws':
        return proxy_request(BACKEND_URL, '/ws')
    return proxy_request(FRONTEND_URL, '/' + path)

def proxy_request(base_url, path):
    try:
        url = base_url + path
        resp = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30
        )
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items() if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return f"Proxy error: {e}", 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
