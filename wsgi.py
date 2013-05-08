import sys

class WSGIWrapper:
    def start_response(self, status, header):
        self.status = status
    def run(self, app, env, out=sys.stdout):
        self.status = ''
        for chunk in app(env, self.start_response):
            out.write(chunk)
        if 'rc' in env:
            sys.exit(env['rc'])
        return self.status
