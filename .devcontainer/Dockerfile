FROM ubuntu:26.04

ARG USERNAME=ubuntu
ARG USER_UID=1000
ARG USER_GID=${USER_UID}

ENV DEBIAN_FRONTEND=noninteractive

RUN chown root:root /tmp \
    && chmod 1777 /tmp

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        apt-transport-https \
        bash-completion \
        bubblewrap \
        build-essential \
        ca-certificates \
        curl \
        file \
        g++ \
        gcc \
        git \
        git-lfs \
        gnupg \
        gpg-agent \
        jq \
        less \
        libc6-dev \
        libffi-dev \
        libssl-dev \
        lsb-release \
        make \
        nano \
        openssh-client \
        pkg-config \
        procps \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
        rsync \
        shellcheck \
        software-properties-common \
        sudo \
        tar \
        tig \
        time \
        tzdata \
        unzip \
        vim \
        wget \
        xz-utils \
        zip \
        zsh \
        zstd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN usermod --shell /bin/bash "${USERNAME}" \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${USERNAME}" \
    && chmod 0440 "/etc/sudoers.d/${USERNAME}"

RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g npm \
    && npm install -g @anthropic-ai/claude-code \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER ${USERNAME}

RUN curl -LsSf https://astral.sh/uv/install.sh | sh