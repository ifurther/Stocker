# Define a build-time argument with a default value for base container images.
ARG UV_VER=0.5.24
ARG DEBIAN_VER=bookworm
ARG WORKSPACE_NAME_=workspace
ARG PROJECT_NAME_=${PROJECT_NAME}

# Multi-Stage Build: Despite using two base images, only one container is built and run.
# The final container is based on the second image, while copying content from the uv stage into the final stage.
# FROM ghcr.io/astral-sh/uv:python3.12-bookworm
FROM ghcr.io/astral-sh/uv:$UV_VER AS uv

FROM mcr.microsoft.com/vscode/devcontainers/base:$DEBIAN_VER

# Install/Update linux packages; install common dev tools like: git, process tools, ...
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends\
    procps \
    build-essential \
    curl \
    swig \
    wget \
    # For OpenCV etc...
    libgl1 libglib2.0-0 \
    # To reduce the image size, it is recommended refresh the package cache as follows.
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copies files or directories from the uv stage into the final stage,
# and ensures that the ownership of the copied files is adjusted to the user and group in the final image,
# and making its functionality or binaries available in the final container.
COPY --from=uv --chown=vscode: /uv /uvx /bin/

WORKDIR /vscode/${WORKSPACE_NAME_}

# The code to run when container is started:
# Common practice to keep the Docker container running without performing any significant action.
ENTRYPOINT ["tail", "-f", "/dev/null"]
