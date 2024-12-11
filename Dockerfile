# Use a lightweight Linux base image
FROM debian:bookworm-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Setup phase
RUN apt-get update && apt-get install -y --no-install-recommends wget build-essential && \
    wget http://ftp.gnu.org/gnu/libc/glibc-2.38.tar.gz && \
    tar -xvzf glibc-2.38.tar.gz && cd glibc-2.38 && \
    mkdir build && cd build && ../configure --prefix=/usr && make && make install && \
    apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && \
    pip install --no-cache-dir --upgrade pip && \
    rm -rf /var/lib/apt/lists/* /glibc-2.38*  # Cleanup to reduce image size

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose application port (if needed)
# EXPOSE 8000

# Start phase
CMD ["python3", "main.py"]
