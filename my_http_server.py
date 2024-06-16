from random import randint
import socket
from attr import dataclass
import json

HOST = "127.0.0.1"
PORT = randint(1023, 6900)

type Router = dict[str, Router | str]


@dataclass
class RequestData:
    method: str
    route: str
    version: str


@dataclass
class ResponseData:
    version: str
    statusCode: int
    statusText: str
    payload: str | None


@dataclass
class HTTPError(Exception):
    statusCode: int
    statusText: int


def request_parser(request: bytes) -> RequestData:
    """takes the raw bytes of a request and parses it into a data object

    Args:
        request (bytes): the bytes of the request

    Returns:
        RequestData: _description_
    """

    # break down the request
    request_str = request.decode("utf-8")
    request_lines = request_str.split("\r\n")

    assert len(request_lines) > 0

    # read the first line to determine method, path, and version

    [method, path, version] = request_lines[0].split(" ")

    assert method in ["GET", "POST"]

    return RequestData(method, path, version)


def request_resolver(request: RequestData) -> ResponseData:
    """takes a request object and resolves it into a response

    Args:
        request (RequestData): _description_

    Returns:
        ResponseData: _description_
    """

    # handle the method type
    match request.method:
        case "GET":
            index = open("index.html", encoding="utf-8").read()
            return ResponseData(request.version, 200, "OK", index)

        case _:
            return ResponseData(request.version, 405, "Method Not Allowed", None)


def route_resolver(path: str) -> str:
    """takes an HTTP 'path' and resolves it into an actual filepath

    Args:
        path (str): _description_

    Returns:
        str: _description_
    """

    # split the path by slashes
    path_steps = path.split("/")

    # retrieve the dictionary containing all routings
    with open("address-resolver.json", encoding="utf-8") as router:
        route_dict = json.load(router)

        # handle the case for the root route
        if len(path_steps) == 0:
            return route_dict["index"]

        # otherwise, recursively dive into the router
        def find_route(curr_router: Router, path_steps: list[str]) -> Router | str:
            if len(path_steps) == 1:
                return curr_router[path_steps[0]]

            # if we find an ending for the route when we do not expect it (path has not been fully consumed, raise an error)
            if isinstance(new_router := curr_router[path_steps[0]], str):
                raise KeyError
            return find_route(new_router, path_steps[1:])


def response_builder(response: ResponseData) -> bytes:
    """takes response data and converts it into bytes for sending

    Args:
        response (ResponseData): _description_

    Returns:
        bytes: _description_
    """
    response_string: str = (
        f"{response.version} {response.statusCode} {response.statusText}\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{response.payload}"
    )
    return response_string.encode()


if __name__ == "__main__":
    print(f"Launching with {PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Serving requests from {addr}")
                data = conn.recv(1024)
                print(data)
                response_data: ResponseData
                if not data:
                    break
                try:
                    request_data = request_parser(data)
                    response_data = request_resolver(request_data)
                except AssertionError:
                    response_data = ResponseData("HTTP/1.1", 400, "Bad Request", None)
                conn.sendall(response_builder(response_data))
