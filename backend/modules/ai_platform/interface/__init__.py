"""The AI Platform's HTTP surface.

Deliberately one endpoint, and deliberately a **read**. The platform produces
narrations from a use case invoked by the pipeline; nothing here triggers a
model call, because §7 forbids an API handler blocking on pipeline work and a
narration is a ~20-second inference.
"""
