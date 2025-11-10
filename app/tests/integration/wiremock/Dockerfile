FROM wiremock/wiremock:3.3.1

# Copy mappings to container
COPY mappings /home/wiremock/mappings

# Default command with options
CMD ["--global-response-templating", "--verbose"]

