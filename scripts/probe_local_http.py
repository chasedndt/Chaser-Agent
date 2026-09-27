"""Explicit public/toy live smoke; creates one pending review, never an approval."""
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

from chaser_agent.local_acl import read_private_control_token


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    token = read_private_control_token(args.data_dir)
    base = f'http://127.0.0.1:{args.port}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(path, payload=None, *, auth=True, extra=None):
        headers = {'Authorization': f'Bearer {token}'} if auth else {}
        headers.update(extra or {})
        data = None if payload is None else json.dumps(payload).encode()
        if data is not None:
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(base + path, data, headers)
        try:
            with opener.open(req, timeout=30) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    health_status, health = request('/v1/health', auth=False)
    assert health_status == 200
    text = 'The operator reviews proposed actions before execution.'
    created, body = request('/v1/source-cards', {
        'title': 'Approved runtime repair smoke', 'text': text,
        'privacy_class': 'public_toy', 'profile': 'general_source_review',
    })
    assert created == 201, (created, body)
    run = json.loads(body)
    path = '/v1/runs/' + run['run_id']
    index_status, index_body = request(path)
    assert index_status == 200
    index = json.loads(index_body)
    source_status, source = request(path + '/artifacts/original_source.md')
    assert source_status == 200 and source.decode().strip() == text
    no_token, _ = request(path, auth=False)
    bad_origin, _ = request(path, extra={'Origin': 'https://example.invalid'})
    no_executor, _ = request('/v1/hud/controls', {'session_id': 'absent', 'command': 'pause'})
    assert no_token == 401 and bad_origin == 403 and no_executor == 409
    print(json.dumps({'health': json.loads(health), 'run_id': run['run_id'],
                      'created': created, 'index': index_status,
                      'integrity_status': index.get('integrity_status'),
                      'exact_source_roundtrip': True, 'no_token': no_token,
                      'untrusted_origin': bad_origin, 'no_executor': no_executor,
                      'human_review': 'pending'}, indent=2))


if __name__ == '__main__':
    main()
