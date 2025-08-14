FROM python:3.11-slim

WORKDIR /app
# Set the working directory within the container to /app for any subsequent commands
# Copy the entire current directory contents into the container at /app
COPY . /app/

# install deps
RUN apt update && apt install git libpq-dev python3-dev  -y
RUN apt-get install gcc -y

# Install required packages for downloading and extracting
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/*


## chrome components
RUN apt-get update && apt-get install -y \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1

# Set environment variables for the versions/URLs
ENV CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.108/linux64/chrome-linux64.zip"
ENV CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.108/linux64/chromedriver-linux64.zip"

## Chromedriver chrome compatibility
## https://googlechromelabs.github.io/chrome-for-testing/#stable


# Download and install Chrome for Testing
# ENV /app/.apt/usr/bin/google-chrome
#$RUN set -e && \

## these never worked anyways -- mkdir and cp commands just blanked.
# RUN wget -O /tmp/chrome-linux64.zip $CHROME_URL
# RUN unzip /tmp/chrome-linux64.zip -d /usr/local/
# RUN mkdir -p /app/.apt/usr/bin
# RUN cp /usr/local/chrome-linux64/chrome /app/.apt/usr/bin/google-chrome
# RUN  rm -rf /tmp/chrome-linux64
# RUN chmod +x /app/.apt/usr/bin/google-chrome



    # The extracted folder usually contains a "chrome" binary inside "chrome-linux64/"
    # Move it to a more standard location or symlink it.
#     mv /usr/local/chrome-linux64 /usr/local/chrome && \
#     ln -s /usr/local/chrome/chrome /usr/local/bin/chrome

# Download and install ChromeDriver for the matching version
## env default /app/.chromedriver/bin/chromedriver
# RUN set -e && \
#     wget -qO /tmp/chromedriver-linux64.zip $CHROMEDRIVER_URL && \
#     unzip /tmp/chromedriver-linux64.zip -d /usr/local/ && \
#     #rm /tmp/chromedriver-linux64.zip && \
#     mkdir -p /app/.chromedriver/bin && \
#     mv /usr/local/chromedriver-linux64  /app/.chromedriver/bin/chromedriver && \
#     chmod +x /app/.chromedriver/bin/chromedriver

# RUN wget -qO /tmp/chromedriver-linux64.zip $CHROMEDRIVER_URL
# RUN unzip /tmp/chromedriver-linux64.zip -d /usr/local/
# RUN test -f /usr/local/chromedriver-linux64/chromedriver || (echo "Chromedriver not extracted" && exit 1)
#
# RUN mkdir -p /app/.chromedriver/bin
# RUN test -d /app/.chromedriver/bin || (echo "Destination directory not created" && exit 1)
#
# RUN mv /usr/local/chromedriver-linux64/chromedriver  /app/.chromedriver/bin/chromedriver
# RUN test -f /app/.chromedriver/bin/chromedriver || (echo "Chromedriver not moved to destination" && exit 1)
#
# RUN chmod +x /app/.chromedriver/bin/chromedriver


    # The extracted directory is "chromedriver-linux64/", inside is "chromedriver" binary.
#     mv /usr/local/chromedriver-linux64 /usr/local/chromedriver && \
#     chmod +x /usr/local/chromedriver/chromedriver && \
#     ln -s /usr/local/chromedriver/chromedriver /usr/local/bin/chromedriver


# Upgrade pip to ensure we have the latest version for installing dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
#RUN python manage.py collectstatic --noinput


ENV PYTHONUNBUFFERED=1