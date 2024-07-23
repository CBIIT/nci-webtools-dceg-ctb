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
    && dnf clean all

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

ENV PORT=8080


# Install cron and setup cron job
RUN dnf install -y cronie \
    && (crontab -l 2>/dev/null; echo "* 1 * * * /usr/local/bin/python /app/ctb/cron/cron_job.py >> /var/log/cron.log 2>&1") | crontab \
    && touch /var/log/cron.log

CMD gunicorn --bind 0.0.0.0:$PORT ctb.wsgi


