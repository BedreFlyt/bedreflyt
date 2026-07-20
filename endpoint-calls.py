import urllib.request
import time
import socket

# Check the status, if I don't get a 200 response, the server is still starting up
response = urllib.request.urlopen("http://localhost:8090/api/v1/status")

while response.getcode() != 200:
    print("Server is still starting up, please wait...")
    time.sleep(30)  # Wait for 30 seconds before retrying
    response = urllib.request.urlopen("http://localhost:8090/api/v1/status")

print("Server is up and running!")

# Handle timeout
try:
    socket.setdefaulttimeout(600)  # Set a timeout of 600 seconds for all socket operations
    urllib.request.urlopen("http://localhost:8090/api/v1/fuseki/rooms")
    urllib.request.urlopen("http://localhost:8090/api/v1/fuseki/diagnosis")
    urllib.request.urlopen("http://localhost:8090/api/v1/fuseki/tasks")
    urllib.request.urlopen("http://localhost:8090/api/v1/fuseki/treatments")
    urllib.request.urlopen("http://localhost:8090/api/v1/fuseki/wards")

    print("All endpoints have been successfully called.")
except socket.timeout:
    print("Request timed out.")
