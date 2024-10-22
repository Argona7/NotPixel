import os
import base64

def generate_random_string(length=8):
    characters = 'abcdef0123456789'
    random_string = ''
    for _ in range(length):
        random_index = int((len(characters) * int.from_bytes(os.urandom(1), 'big')) / 256)
        random_string += characters[random_index]
    return random_string

def generate_session_id() -> str:
    session_id = '-'.join([
        generate_random_string(8), generate_random_string(4), '4' + generate_random_string(3),
        generate_random_string(4), generate_random_string(12)])
    return session_id

def generate_sec_websocket_key():
    random_bytes = os.urandom(16)
    sec_websocket_key = base64.b64encode(random_bytes).decode('utf-8')
    return sec_websocket_key