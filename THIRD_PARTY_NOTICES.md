# Third Party Notices

This project integrates an OpenMAIC-compatible interactive classroom capability through `backend/services/openmaic_classroom_client.py`.

- OpenMAIC is treated as an external classroom rendering and generation service.
- The backend calls `OPENMAIC_CLASSROOM_SERVICE_URL` when that service is available.
- For contest demos and local development, the adapter includes a local fallback classroom for the "gradient descent and learning rate" scenario, so the main platform remains runnable without bundling OpenMAIC source code.
- Generated classroom records are stored as first-class course resources with `resource_type = "interactive_classroom"` and learning tasks with `task_type = "interactive_classroom"`.

Teams using a real OpenMAIC deployment should review and comply with that project's own license and attribution requirements.
