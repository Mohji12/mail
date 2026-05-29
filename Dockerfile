# Platform comes from the build command (--platform linux/amd64 in build-lambda.ps1), not here,
# so Docker does not warn about FROM --platform=linux/amd64. Lambda x86_64 = amd64 image.
#
# If AWS shows ImageLayerFailure: use build-lambda.ps1 (attestations off) or build-lambda-legacy.ps1.
FROM public.ecr.aws/lambda/python:3.11

# Set the working directory in the container
WORKDIR /var/task

# Copy the requirements file into the container
COPY requirements.txt .

# One RUN = fewer buildkit round-trips (helps avoid "rpc error ... EOF" on Docker Desktop during long pip steps)
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
RUN pip install --upgrade pip wheel setuptools \
    && pip install --no-cache-dir --only-binary=:all: -r requirements.txt -t .

# Copy the entire application into the container
COPY app/ ./app

# Set the Lambda handler (app.main.handler points to the `handler` in main.py)
CMD ["app.main.handler"]
