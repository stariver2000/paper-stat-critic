"""Pipeline stages. Each stage is a pure function from model objects to model objects.

Stages never read or write files and never import one another; the
pipeline package wires their outputs together.
"""
