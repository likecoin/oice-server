FROM python:3.9-alpine
RUN mkdir /app
RUN apk --no-cache add \
  ffmpeg \
  git \
  imagemagick \
  unzip \
  zip
COPY ./requirements.txt /app/
WORKDIR /app
RUN apk --no-cache --virtual .build-deps add \
  gcc \
  g++ \
  linux-headers \
  musl-dev \
  && pip install --upgrade pip \
  && pip install setuptools==45 \
  && pip install -r requirements.txt \
  && apk del .build-deps
COPY ["CHANGES.txt", \
  "README.md", \
  "setup.py", \
  "/app/"]
COPY *.ini /app/
RUN python setup.py develop
COPY . /app
CMD pserve
