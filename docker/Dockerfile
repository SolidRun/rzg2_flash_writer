# Start with a minimal base image
FROM debian:stable-slim

# Set environment variables
ENV TOOLCHAIN_URL=https://developer.arm.com/-/media/Files/downloads/gnu/13.3.rel1/binrel/arm-gnu-toolchain-13.3.rel1-x86_64-aarch64-none-linux-gnu.tar.xz \
    TOOLCHAIN_DIR=/opt/arm-toolchain \
    PATH=$PATH:/opt/arm-toolchain/bin

# Install necessary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    xz-utils \
    ca-certificates \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Download and extract the ARM toolchain
RUN mkdir -p $TOOLCHAIN_DIR && \
    wget -qO- $TOOLCHAIN_URL | tar -xJ --strip-components=1 -C $TOOLCHAIN_DIR

# Set default shell to bash for convenience
SHELL ["/bin/bash", "-c"]

# Define the default command to keep the container running
CMD ["bash"]
