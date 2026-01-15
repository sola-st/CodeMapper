FROM python:3.10-slim

WORKDIR /codemapper_home

# Install system dependencies (optional: update pip + install build deps)
RUN apt-get update && apt-get install -y \
    git \
    && pip install --upgrade pip

COPY . /codemapper_home

# Install dependencies
RUN pip install -r requirements.txt

RUN pip install -e .

CMD ["/bin/bash"]