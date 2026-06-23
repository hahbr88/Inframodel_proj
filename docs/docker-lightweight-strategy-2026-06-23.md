# Docker Lightweight Strategy

## Scope

- `apps/admin-web`
- `apps/service-web`
- `apps/integrated-was`

## Strategy

Frontend images already use a multi-stage Node build and an nginx Alpine
runtime. The final image only contains nginx, the SPA build output, and the
nginx config, so there is little safe size reduction left without changing the
static server behavior.

The WAS image had the largest opportunity. The optimized Dockerfile switches
from Debian slim to Alpine, keeps build tools in the builder stage only,
installs Python dependencies without bytecode, removes pip/setuptools/wheel
from the runtime venv, and runs the app as an unprivileged user.

## Measured Result

Local runnable image size:

- `infra-lightcheck-was:local`: 360MB
- `infra-lightopt-was:local`: 193MB
- `infra-lightcheck-admin:local`: 78.1MB
- `infra-lightopt-admin:local`: 78.1MB
- `infra-lightcheck-service:local`: 78.2MB
- `infra-lightopt-service:local`: 78.2MB

Compressed size comparable to what ECR shows:

- `infra-lightopt-admin:local`: 21.85MB
- `infra-lightopt-service:local`: 21.85MB
- `infra-lightopt-was:local`: 46.33MB

## Verification

- `infra-lightopt-was:local` builds successfully on `python:3.12-alpine`.
- `boto3`, `asyncmy`, and `sqlalchemy` import successfully.
- FastAPI app import succeeds.
- WAS root endpoint returns a healthy JSON response from inside the container.
- `infra-lightopt-admin:local` nginx config test succeeds.
- `infra-lightopt-service:local` nginx config test succeeds.

## Tradeoff

The WAS image now runs on Alpine/musl instead of Debian/glibc. This is a good
size win, but it should be validated in the deployed environment before
replacing the current production tag.

