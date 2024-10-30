FROM python:3.7-alpine

RUN apk add --update --no-cache supervisor python3-dev

RUN python -m pip install --upgrade pip

COPY requirements.txt /requirements.txt
RUN python -m pip install -r requirements.txt

RUN adduser -D -u 1000 -g 1000 -s /bin/sh www

COPY flag.txt /flag.txt

RUN mkdir -p /app

WORKDIR /app

COPY src .
RUN chown -R www:www .

COPY supervisord.conf /etc/supervisord.conf

EXPOSE 3000

ENV PYTHONDONTWRITEBYTECODE=1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
