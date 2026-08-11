"""Provider-neutral inference boundary (Layer 12).

No module in this package imports a provider SDK, opens a network connection, or
reads a credential. The only adapter shipped in P0.1 is a scripted fake used to
exercise and stress the request/response envelope before any live provider is
approved.
"""
