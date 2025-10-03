FROM public.ecr.aws/amazonlinux/amazonlinux:2023

RUN dnf -y update && \
    dnf -y install \
    gcc \
    mariadb105 \
    mariadb105-devel \
    pkgconf \
    pkgconf-pkg-config \
    python3-devel \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    cairo-devel \
    cairo-gobject-devel \
    gobject-introspection-devel \
    pkg-config \
    && dnf clean all

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

ENV PORT=8080

ENV DJANGO_SETTINGS_MODULE=ctb.settings

CMD touch .env && cat .env && gunicorn --bind 0.0.0.0:$PORT ctb.wsgi
