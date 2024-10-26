import os
import base64
from PIL.ImageFile import ImageFile
from utils.protobuf import client_pb2 as protocol
from inflate64 import Inflater

def generate_random_string(length = 8) -> str:
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

def generate_sec_websocket_key() -> str:
    random_bytes = os.urandom(16)
    sec_websocket_key = base64.b64encode(random_bytes).decode('utf-8')
    return sec_websocket_key

def image_to_matrix(image: ImageFile) -> dict[tuple[int, int], str]:
    matrix = {}
    rgb_img = image.convert('RGB')
    width, height = rgb_img.size
    for y in range(height):
        for x in range(width):
            r, g, b = rgb_img.getpixel((x, y))
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            matrix[(x, y)] = hex_color
    return matrix

def varint_decode(buffer: bytes, position: int):
    """Decode a varint from buffer starting at position."""
    result = 0
    shift = 0
    while True:
        byte = buffer[position]
        position += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            break
    return result, position

def decode_protobuf(data: bytes) -> list[protocol.Reply]:
    replies = []
    position = 0
    while position < len(data):
        message_length, position = varint_decode(data, position)
        message_end = position + message_length
        message_bytes = data[position:message_end]
        position = message_end
        reply = protocol.Reply()
        reply.ParseFromString(message_bytes)
        replies.append(reply)
    return replies

def decompress_data(data: bytes) -> bytes:
    decompressor = Inflater()
    extracted = decompressor.inflate(data)
    return extracted