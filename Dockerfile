# Use a lightweight Linux base image
FROM debian:bookworm-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Setup phase
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget build-essential gawk bison python3 python3-pip && \
    wget http://ftp.gnu.org/gnu/libc/glibc-2.38.tar.gz && \
    tar -xvzf glibc-2.38.tar.gz && cd glibc-2.38 && \
    mkdir build && cd build && ../configure --prefix=/usr && make && make install && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /glibc-2.38*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

# Expose application port (if needed)
# EXPOSE 8000

# Start phase
CMD ["python3", "main.py"]
