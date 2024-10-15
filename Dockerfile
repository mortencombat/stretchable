# This image runs tests from test_node on Ubuntu and lowest supported Python version (currently 3.8)
FROM ubuntu:latest

# Install tzdata
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata

# Install Rust/Cargo
RUN apt-get install -y curl gcc
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH=/root/.cargo/bin:$PATH
RUN echo ls -l /root/.cargo/bin
RUN cargo version

# Install Python
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get update
ARG pyver=3.8
RUN apt-get install -y python${pyver} python${pyver}-venv

# Build and install stretchable
WORKDIR /app
COPY . .
RUN python${pyver} -m venv .venv
RUN .venv/bin/pip install ".[test]"

# Run tests
RUN .venv/bin/pytest tests/test_node.py
