# Welcome to myHTTPServer-Python

This is an experimental HTTP Server project by me written in Python for the funzies. The main goal of this project is for me to better understand the Hypertext Transfer Protocol (HTTP). It's been said that one great way to learn a language is to code an HTTP server in it, but for me, before I could do that I thought it'd be nice to write learn HTTP servers by coding in a language that I knew quite well. Hence, Python.

## Objectives

The initial objectives of this project are as follows:
- To write a program that serves HTTP documents over Transmission Control Protocol (TCP) sockets

The additional side objectives I hit along the way are as follows:
- Providing a routing system in JSON that:
  - Allows the backend to locate and serve resources
  - Catches accesses to missing resources and responds with 404's
- Making use of any open TCP socket through socket 0
- Implement network IO concurrency (WIP)

## Reflections

This project is mostly a stepping stone for me to begin writing this in languages like Rust and possibly even Haskell, but I'd say I learned a bit along the way. My key lesson from this activity is that HTTP is literally just about exchanging well-formatted 'text documents' over TCP sockets.

From here, the next obvious step is to simply port this implementation into whatever language I want. However, one thing I do want to know now is how do web browsers function as HTML renderers. I'm sure my humble little HTTP server is accessible via my browser, but now I also wonder about the mechanics of the browser registering a URL in its address bar and then rendering a full webpage.