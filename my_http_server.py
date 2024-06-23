import socket
import selectors
from attr import dataclass
import json

HOST = "127.0.0.1"
PORT = 0

sel = selectors.DefaultSelector()

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
    statusText: str


@dataclass
class SocketData:
    addr: str
    inb: bytes
    outb: bytes


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
    print(request_lines)

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
            payload = open(route_resolver(request.route), encoding="utf-8").read()
            return ResponseData(request.version, 200, "OK", payload)

        case _:
            return ResponseData(request.version, 405, "Method Not Allowed", None)


def route_resolver(path: str) -> str:
    """takes an HTTP 'path' and resolves it into an actual filepath

    Args:
        path (str): _description_

    Returns:
        str: _description_
    """

    # split the path by slashes, not including the initial blank path step and catching the "/" case
    path_steps = path.split("/")[1:] if path != "/" else []

    # retrieve the dictionary containing all routings
    with open("address-resolver.json", encoding="utf-8") as router:
        route_dict = json.load(router)

        # handle the case for the root route
        if len(path_steps) == 0:
            return route_dict["index"]

        # otherwise, recursively dive into the router
        def find_route(curr_router: Router, path_steps: list[str]) -> Router | str:
            if len(path_steps) <= 1:
                return curr_router[path_steps[0]]

            # if we find an ending for the route when we do not expect it (path has not been fully consumed, raise an error)
            if isinstance(new_router := curr_router[path_steps[0]], str):
                raise KeyError
            return find_route(new_router, path_steps[1:])

        try:
            route = find_route(route_dict, path_steps)
        except KeyError as exc:
            raise HTTPError(404, "Not Found") from exc

        if isinstance(route, dict):
            # if we find that the returned route is another dict, ensure that there is an index
            if isinstance(index := route["index"], str):
                return index
            raise HTTPError(404, "Not Found")

        return route


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


def service_conn(service_key: selectors.SelectorKey, event_mask):  # type: ignore
    conn: socket.socket = service_key.fileobj  # type: ignore
    data: SocketData = service_key.data
    if event_mask & selectors.EVENT_READ:
        read_data = conn.recv(4096)
        if not read_data:
            print(f"Closing connection to {data.addr}")
            sel.unregister(conn)
            conn.close()
            return
        data.inb += read_data

        # if the last bytes of inbound data are not valid terminators for HTTP, return and keep reading
        if data.inb[-4:] != b"\r\n\r\n":
            return
        try:
            request_data = request_parser(data.inb)
            response_data = request_resolver(request_data)
        except AssertionError:
            response_data = ResponseData(
                "HTTP/1.1", 400, "Bad Request", "400 Bad Request"
            )
        except HTTPError as err:
            response_data = ResponseData(
                "HTTP/1.1",
                err.statusCode,
                err.statusText,
                f"{err.statusCode} {err.statusText}",
            )
        data.outb += response_builder(response_data)
        data.inb = b""
    if event_mask & selectors.EVENT_WRITE:
        conn.sendall(data.outb)
        data.outb = b""


def accept_conn(sock: socket.socket):
    conn, addr = sock.accept()
    print(f"New connection opened for {addr}")
    conn.setblocking(False)
    data = SocketData(addr, b"", b"")
    sel.register(conn, selectors.EVENT_WRITE | selectors.EVENT_READ, data=data)


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        print(f"Launching with {s.getsockname()}")
        s.listen()
        s.setblocking(False)
        sel.register(s, selectors.EVENT_READ, data=None)
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:

                # if the connection is new, accept and register the connection
                if not key.data:
                    accept_conn(key.fileobj)  # type: ignore

                # if the connection is not new, process it
                else:
                    service_conn(key, mask)
