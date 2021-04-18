FROM python:3.9-slim-buster as requirements
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements requirements
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements/bot.txt

FROM python:3.9-slim-buster
RUN useradd -m -s /bin/bash -U appuser
USER appuser
COPY --from=requirements /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY core core
COPY bot bot
CMD python -m bot
