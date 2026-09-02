"""Tool / MCP capability boundary (Layer 13).

Tools are the more dangerous authority surface than providers: a model reply is
text, but a tool call has side effects on the filesystem, the network, accounts,
and money. This package declares what a tool is *allowed* to do and refuses
anything outside that declaration. Nothing here executes a tool; P0.1 authorizes
and plans only, and execution raises.
"""
