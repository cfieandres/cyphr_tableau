The general syntax is:

spec:
  containers:                           # container list
  - name: <name>
    image: <image-name>
    command:                            # optional list of strings
      - <cmd>
      - <arg1>
    args:                               # optional list of strings
      - <arg2>
      - <arg3>
      - ...
    env:                                # optional
        <key>: <value>
        <key>: <value>
        ...
    readinessProbe:                     # optional
        port: <TCP port-num>
        path: <http-path>
    volumeMounts:                       # optional list
      - name: <volume-name>
        mountPath: <mount-path>
      - name: <volume-name>
        ...
    resources:                          # optional
        requests:
          memory: <amount-of-memory>
          nvidia.com/gpu: <count>
          cpu: <cpu-units>
        limits:
          memory: <amount-of-memory>
          nvidia.com/gpu: <count>
          cpu: <cpu-units>
    secrets:                                # optional list
      - snowflakeSecret:
          objectName: <object-name>         # specify this or objectReference
          objectReference: <reference-name> # specify this or objectName
        directoryPath: <path>               # specify this or envVarName
        envVarName: <name>                  # specify this or directoryPath
        secretKeyRef: username | password | secret_string # specify only with envVarName
  endpoints:                             # optional endpoint list
    - name: <name>
      port: <TCP port-num>                     # specify this or portRange
      portRange: <TCP port-num>-<TCP port-num> # specify this or port
      public: <true / false>
      protocol : < TCP / HTTP >
      corsSettings:                  # optional CORS configuration
        Access-Control-Allow-Origin: # required list of allowed origins, for example, "http://example.com"
          - <origin>
          - <origin>
            ...
        Access-Control-Allow-Methods: # optional list of HTTP methods
          - <method>
          - <method>
            ...
        Access-Control-Allow-Headers: # optional list of HTTP headers
          - <header-name>
          - <header-name>
            ...
        Access-Control-Expose-Headers: # optional list of HTTP headers
          - <header-name>
          - <header-name>
            ...
    - name: <name>
      ...
  volumes:                               # optional volume list
    - name: <name>
      source: local | @<stagename> | memory | block
      size: <bytes-of-storage>           # specify if memory or block is the volume source
      blockConfig:                       # optional
        initialContents:
          fromSnapshot: <snapshot-name>
        iops: <number-of-operations>
        throughput: <MiB per second>
      uid: <UID-value>                   # optional, only for stage volumes
      gid: <GID-value>                   # optional, only for stage volumes
    - name: <name>
      source: local | @<stagename> | memory | block
      size: <bytes-of-storage>           # specify if memory or block is the volume source
      ...
  logExporters:
    eventTableConfig:
      logLevel: <INFO | ERROR | NONE>
  platformMonitor:                      # optional, platform metrics to log to the event table
    metricConfig:
      groups:
      - <group-1>
      - <group-2>
      ...
capabilities:
  securityContext:
    executeAsCaller: <true / false>     # optional, indicates whether application intends to use caller’s rights
serviceRoles:                   # Optional list of service roles
- name: <service-role-name>
  endpoints:
  - <endpoint_name1>
  - <endpoint_name2>
  - ...
- ...
Note that the spec and serviceRoles are the top-level fields in the specification.

spec: Use this field to provide specification details. It includes these top-level fields:

spec.containers (required): A list of one or more application containers. Your containerized application must have at least one container.

spec.endpoints (optional): A list of endpoints that the service exposes. You might choose to make an endpoint public, allowing network ingress access to the service.

spec.volumes (optional): A list of storage volumes for the containers to use.

spec.logExporters (optional): This field manages the level of container logs exported to the event table in your account.

serviceRoles: Use this field to define one or more service roles. The service role is the mechanism you use to manage privileges to endpoints the service exposes.

General guidelines
The following format guidelines apply for the name fields (container, endpoint, and volume names):

Can be up to 63 characters long.

Can contain a sequence of lowercase alphanumeric or - characters.

Must start with an alphabetic character.

Must end with an alphanumeric character.

Customers should ensure that no personal data, sensitive data, export-controlled data, or other regulated data is entered as metadata in the specification file. For more information, see Metadata Fields in Snowflake.

The following sections explain each of the top-level spec fields.

spec.containers field (required)
Use the spec.containers field to describe each of the OCI containers in your application.

Note the following:

When you create a service, Snowflake runs these containers on a single node in the specified compute pool, sharing the same network interface.

You might choose to run multiple service instances to load-balance incoming requests. Snowflake might choose to run these service instances on the same node or different nodes in the specified compute pool. All containers for a given instance always run on one node.

Currently, Snowpark Container Services requires linux/amd64 platform images.

The following sections explain the types of containers fields.

containers.name and containers.image fields
For each container, only name and image are required fields.

name is the image name. This name can be used to identify a specific container for the purposes of observability (for example, logs, metrics).

image is the name of the image you uploaded to a Snowflake image repository in your Snowflake account.

For example:

spec:
  containers:
    - name: echo
      image: /tutorial_db/data_schema/tutorial_repository/echo_service:dev
containers.command and containers.args fields
Use these optional fields to control what executable is started in your container and the arguments that are passed to that executable. You can configure defaults for these at the time of creating the image, typically in a Dockerfile. Using these service specification fields let you to change these defaults (and thus change the container behavior) without having to rebuild your container image:

containers.command overrides the Dockerfile ENTRYPOINT. This allows you to run a different executable in the container.

containers.args overrides the Dockerfile CMD. This allows you to provide different arguments to the command (the executable).

Example

Your Dockerfile includes the following code:

ENTRYPOINT ["python3", "main.py"]
CMD ["Bob"]
These Dockerfile entries execute the python3 command and pass two arguments: main.py and Bob. You can override these values in the specification file as follows:

To override the ENTRYPOINT, add the containers.command field in the specification file:

spec:
  containers:
  - name: echo
    image: <image_name>
    command:
    - python3.9
    - main.py
To override the argument “Bob”, add the containers.args field in the specification file:

spec:
  containers:
  - name: echo
    image: <image_name>
    args:
      - Alice
containers.env field
Use the containers.env field to define container environment variables. All processes in the container have access to these environment variables:

spec:
  containers:
  - name: <name>
    image: <image_name>
    env:
      ENV_VARIABLE_1: <value1>
      ENV_VARIABLE_2: <value2>
      …
      …
Example

In Tutorial 1, the application code (echo_service.py) reads the environment variables as shown:

CHARACTER_NAME = os.getenv('CHARACTER_NAME', 'I')
SERVER_PORT = os.getenv('SERVER_PORT', 8080)
Note that the example passes default values for the variables to the getenv function. If the environment variables are not defined, these defaults are used.

CHARACTER_NAME: When the Echo service receives an HTTP POST request with a string (for example, “Hello”), the service returns “I said Hello”. You can overwrite this default value in the specification file. For example, set the value to “Bob”; the Echo service returns a “Bob said Hello” response.

SERVER_PORT: In this default configuration, the Echo service listens on port 8080. You can override the default value and specify another port.

The following service specification overrides both of these environment variable values:

spec:
  containers:
  - name: echo
    image: <image_name>
    env:
      CHARACTER_NAME: Bob
      SERVER_PORT: 8085
  endpoints:
  - name: echo-endpoint
    port: 8085
Note that, because you changed the port number your service listens on, the specification must also update the endpoint (endpoints.port field value) as shown.

containers.readinessProbe field
Use the containers.readinessProbe field to identify a readiness probe in your application. Snowflake calls this probe to determine when your application is ready to serve requests.

Snowflake makes an HTTP GET request to the specified readiness probe, at the specified port and path, and looks for your service to return an HTTP 200 OK status to ensure that only healthy containers serve traffic.

Use the following fields to provide the required information:

port: The network port on which the service is listening for the readiness probe requests. You need not declare this port as an endpoint.

path: Snowflake makes HTTP GET requests to the service with this path.

Example

In Tutorial 1, the application code (echo_python.py) implements the following readiness probe:

@app.get("/healthcheck")
def readiness_probe():
Accordingly, the specification file includes the containers.readinessProbe field:

spec:
  containers:
  - name: echo
    image: <image_name>
    env:
      SERVER_PORT: 8088
      CHARACTER_NAME: Bob
    readinessProbe:
      port: 8088
      path: /healthcheck
  endpoints:
  - name: echo-endpoint
    port: 8088
The port specified by the readiness probe does not have to be a configured endpoint. Your service could listen on a different port solely for the purpose of the readiness probe.

containers.volumeMounts field
Because the spec.volumes and spec.containers.volumeMounts fields work together, they are explained together in one section. For more information, see spec.volumes field (optional).

containers.resources field
A compute pool defines a set of available resources (CPU, memory, and storage) and Snowflake determines where in the compute pool to run your services.

It is recommended that you explicitly indicate resource requirements for the specific container and set appropriate limits in the specification. Note that the resources you specify are constrained by the instance family of the nodes in your compute pool. For more information, see CREATE COMPUTE POOL.

Use containers.resources field to specify explicit resource requirements for the specific application container:

containers.resources.requests: The requests you specify should be the average resource usage you anticipate by your service. Snowflake uses this information to determine placement of the service instance in the compute pool. Snowflake ensures that the sum of the resource requests placed on a given node fits within the available resources on the node.

containers.resources.limits: The limits you specify direct Snowflake to not allocate resources more than the specified limits. Thus, you can prevent cost overruns.

You can specify requests and limits for the following resources:

memory: This is the memory required for your application container. You can use either decimal or binary units to express the values. For example, 2G represents a request for 2,000,000,000 bytes and 2Gi represents a requests for 2 x 1024 x 1024 x 1024 bytes.

When specifying memory, a unit is required. For example, 100M or 5Gi. The supported units are: M, Mi, G, Gi.

cpu: This refers to virtual core (vCPU) units. For example, 1 CPU unit is equivalent to 1 vCPU. Fractional requests are allowed, such as 0.5, which can also be expressed as 500m.

nvidia.com/gpu: If GPUs are required, they must be requested, and there must also be a limit specified for the same quantity. If your container does not specify requests and limits for GPU capacity, it cannot access any GPUs. The number of GPUs you can request is limited by the maximum GPUs supported by the INSTANCE_TYPE you choose when creating a compute pool.

resource.requests and resource.limits are relative to the node capacity (vCPU and memory) of the instance family of the associated compute pool.

If a resource request (cpu, memory, or both) is not provided, Snowflake derives one for you:

For cpu, the derived value is either 0.5 or the cpu limit you provided, whichever is smaller.

For memory, the derived value is either 0.5 GiB or the memory limit you provided, whichever is smaller.

If a resource limit (cpu, memory, or both) is not provided, Snowflake defaults the limits to the node capacity for the instance family of the associated compute pool.

If you do provide resource.limits and they exceed the node capacity, Snowflake will cap the limit to the node capacity.

Snowflake evaluates these resource requirements independently for cpu and memory.

Note that if it’s theoretically impossible for Snowflake to schedule the service on the given compute pool, CREATE SERVICE will fail. Theoretically impossible assumes the compute pool has the maximum number of allowed nodes and there are no other services running on the compute pool. That is, there is no way Snowflake could allocate the requested resources within the compute pool limits. If it’s theoretically possible, but required resources are in use, then CREATE SERVICE will succeed. Some service instances will report status indicating that the service cannot be scheduled due to insufficient resources until resources become available.

Example 1

In the following specification, the containers.resources field describes the resource requirements for the container:

spec:
  containers:
  - name: resource-test-gpu
    image: ...
    resources:
      requests:
        memory: 2G
        cpu: 0.5
        nvidia.com/gpu: 1
      limits:
        memory: 4G
        nvidia.com/gpu: 1
In this example, Snowflake is asked to allocate at least 2 GB of memory, one GPU, and a half CPU core for the container. At the same time, the container is not allowed to use more than 4 GB of memory and one GPU.

Example 2

Suppose:

You create a compute pool of two nodes; each node has 27 GB of memory and one GPU:

CREATE COMPUTE POOL tutorial_compute_pool
  MIN_NODES = 2
  MAX_NODES = 2
  INSTANCE_FAMILY = gpu_nv_s
You create a service that asks Snowflake to run two instances of the service:

CREATE SERVICE echo_service
  MIN_INSTANCES=2
  MAX_INSTANCES=2
  IN COMPUTE POOL tutorial_compute_pool
  FROM @<stage_path>
  SPEC=<spec-file-stage-path>;
Both MIN_INSTANCES and MAX_INSTANCES are set to 2. Therefore, Snowflake will run two instances of the service.

Now, consider these scenarios:

If your service does not explicitly include resource requirements in your application specification, Snowflake decides whether to run these instances on the same node or different nodes in the compute pool.

You do include resource requirements in the service specification and request 10 GB of memory for the container:

- name: resource-test
  image: ...
  resources:
    requests:
      memory: 15G
Your compute pool node has 27 GB of memory, and Snowflake cannot run two containers on the same node. Snowflake will run the two service instances on separate nodes in the compute pool.

You include resource requirements in the service specification and request 1 GB of memory and one GPU for the container:

spec:
  containers:
  - name: resource-test-gpu
    image: ...
    resources:
      requests:
        memory: 2G
        nvidia.com/gpu: 1
      limits:
        nvidia.com/gpu: 1
You are requesting one GPU per container, and each node has only one GPU. In this case, although memory is not an issue, Snowflake cannot schedule both service instances on one node. This requirement forces Snowflake to run the two service instances on two separate compute pool nodes.

containers.secrets field
secrets:                                # optional list
  - snowflakeSecret:
      objectName: <object-name>         # specify this or objectReference
      objectReference: <reference-name> # specify this or objectName
    directoryPath: <path>               # specify this or envVarName
    envVarName: <name>                  # specify this or directoryPath
    secretKeyRef: username | password | secret_string # specify only with envVarName
  - snowflakeSecret: <object-name>      # equivalent to snowflakeSecret.objectName
    ...
Use the containers.secrets field in your service specification to provide Snowflake-managed credentials to your application containers. Start by storing the credentials in Snowflake secret objects. Then, in the service specification, reference the secret object and specify where to place the credentials inside the container.

The following is a summary of how to use the containers.secrets fields:

Specify Snowflake secret: Use the snowflakeSecret field to specify either a Snowflake secret object name or object reference. Object references are applicable when using Snowpark Container Services to create a Native App (an app with containers).

Use secretKeyRef to provide the name of the key in the Snowflake secret.

Specify the secret placement in the application container: Use the envVarName field to pass the secret as environment variables or directoryPath to write the secrets to local container files.

For more information, see Passing credentials to a container using Snowflake secrets.

Note that, the role that is creating the service (owner role) will need the READ privilege on the secrets referenced.

spec.endpoints field (optional)
Use the spec.endpoints field to specify a list of TCP network ports that your application exposes. A service might expose zero to many endpoints. Use the following fields to describe an endpoint:

name: Unique name of the endpoint. The name is used to identify the endpoint in service function and service role specification.

port: The network port on which your service is listening. You must specify this field or the portRange field.

portRange: The network port range on which your application is listening. You must specify this field or the port field.

Ports defined in portRange can only be accessed by directly calling service instance IP addresses. To get service instance IP addresses, use the instances. prefixed DNS name.

instances.<Snowflake_assigned_service_DNS_name>
For more information, see Service-to-service communications.

Note that you can only specify the portRange field if the protocol field is set to TCP and the public field is false.

public: If you want this endpoint to be accessible from the internet, set this field to true. Public endpoints are not supported with the TCP protocol.

protocol: The protocol that the endpoint supports. The supported values are TCP and HTTP. By default, the protocol is HTTP. When specifying the protocol, the following apply:

When this endpoint is public or the target of a service function (see Using a service), the protocol must be HTTP or HTTPS.

The job services require all specified endpoints to use the TCP protocol; HTTP/HTTPS protocols are not supported.

corsSettings: The fields under endpoints allow you to configure Snowflake support for CORS on HTTP requests to public endpoints.

Preview Feature
— Open

Using CORS configuration to enable cross-origin requests to a Snowpark Container Services service is a preview feature.

corsSettings.Access-Control-Allow-Origin: Specifies the origins for which Snowflake responds with the provided CORS allow and expose response headers. The value must be a valid URL with no path specified, for example, https://example.com/, https://example.com:12345, for security reasons the “*” wildcard is not allowed for Access-Control-Allow-Origin.

Snowflake supports the following CORS response headers:

corsSettings.Access-Control-Allow-Methods: Specifies the value of the HTTP Access-Control-Allow-Methods CORS response header. This tells the browsers what HTTP methods (GET, POST, etc.) they should allow when sending requests to this endpoint.

corsSettings.Access-Control-Allow-Headers: Specifies the value of the HTTP Access-Control-Allow-Headers CORS response header. This tells the browsers what HTTP headers they should allow when sending requests to this endpoint.

corsSettings.Access-Control-Expose-Headers: Specifies the value of the HTTP Access-Control-Expose-Headers CORS response header. This tells the browsers what HTTP headers they should allow when exposing responses from this endpoint.

Note

Snowflake performs authentication and authorization checks for public access that allow only Snowflake users that have permission to use the service. Public access to an endpoint requires Snowflake authentication. The authenticated user must also have authorization to this service endpoint (user has usage permission of a role which has access to the endpoint).

Example

The following is the application specification used in Tutorial 1:

spec:
  container:
  - name: echo
    image: <image-name>
    env:
      SERVER_PORT: 8000
      CHARACTER_NAME: Bob
    readinessProbe:
      port: 8000
      path: /healthcheck
  endpoint:
  - name: echoendpoint
    port: 8000
    public: true
This application container exposes one endpoint. It also includes the optional public field to enable access to the endpoint from outside of Snowflake (internet access). By default, public is false.

spec.volumes field (optional)
This section explains both spec.volumes and spec.containers.volumeMounts specification fields because they’re closely related.

spec.volumes defines a shared file system. These volumes can be made available in your containers.

spec.containers.volumeMount defines where a volume appears in specific containers.

Note that, the volumes field is specified at the spec level, but since multiple containers can share the same volume, volumeMounts becomes a spec.containers-level field.

Use these fields to describe both the volumes and volume mounts.

spec.volumes: There can be zero or more volumes. Use the following fields to describe a volume:

Required fields for all volume types:

name: Unique name of the volume. It is referred to by spec.containers.volumeMounts.name.

source: This can be local, memory, block, or "@<stagename>". The next section explains these volume types.

size (required only for the memory and block volume types): For memory and block volumes, this is the size of the volume in bytes. For block storage, the value must always be an integer, specified using the Gi unit suffix. For example, 5Gi means 5*1024*1024*1024 bytes.

For the block type volume, you can specify the following optional fields. For more information, see Specifying block storage in service specification.

blockConfig.initialContents.fromSnapshot: Specify a previously taken snapshot of another volume to initialize the block volume. The snapshot must be in the CREATED state before it can be used to create a volume, or else the service creation will fail. Use the DESCRIBE SNAPSHOT command to get the snapshot’s status.

blockConfig.iops: Specify the number of supported peak input/output operations per second. The supported range 3000-16000 in AWS and 3000-80000 in Azure, with a default of 3000. Note that the data size per operation is capped at 256 KiB for block volumes.

blockConfig.throughput: Specify the peak throughput, in MiB/second, to provision for the volume. The supported range is 125-1000 in AWS and 125-1200 in Azure, with a default of 125.

spec.containers.volumeMounts: Each container can have zero or more volume mounts. containers.volumeMounts is also a list. That is, each container can have multiple volume mounts. Use the following fields to describe a volume mount:

name: The name of the volume to mount. A single container can reference the same volume multiple times.

mountPath: The file path to where the volume for the container should be mounted.

About the supported volume types
Snowflake supports these volume types for application containers to use: local, memory, block, and Snowflake stage.

Local volume: Containers in a service instance can use a local disk to share files. For example, if your application has two containers—an application container and a log analyzer— the application can write logs to the local volume, and the log analyzer can read the logs.

Note that, if you are running multiple instances of a service, only containers belonging to a service instance can share volumes. Containers that belong to different service instances do not share volumes.

Memory: You can use a RAM-backed file system for container use.

Block: Containers can also use block storage volumes. For more information, see Using block storage volumes with services.

Snowflake stage: You can also give containers convenient access to files on a Snowflake stage in your account. For more information, see Using Snowflake stage volumes with services.

Example

Your machine learning application includes the following two containers:

An app container for the main application

A logger-agent container that collects logs and uploads them to Amazon S3

These containers use the following two volumes:

local volume: This application writes logs that the log agent reads.

Snowflake stage, @model_stage: The main application reads files from this stage.

In the following example specification, the app container mounts both the logs and models volumes, and the logging-agent container mounts only the logs volume:

spec:
  containers:
  - name: app
    image: <image1-name>
    volumeMounts:
    - name: logs
      mountPath: /opt/app/logs
    - name: models
      mountPath: /opt/models
  - name: logging-agent
    image: <image2-name>
    volumeMounts:
    - name: logs
      mountPath: /opt/logs
  volumes:
  - name: logs
    source: local
  - name: models
    source: "@model_stage"
If multiple instances of the service are running, the logging-agent and the app containers within a service instance share the logs volume. The logs volume is not shared across service instances.

If, in addition to these volumes, your app container also uses a 2-GB memory volume, revise the specification to include the volume in the volumes list and also add another volume mount in the app containers volumeMounts list:

spec:
  containers:
  - name: app
    image: <image1-name>
    volumeMounts:
    - name: logs
      mountPath: /opt/app/logs
    - name: models
      mountPath: /opt/models
    - name: my-mem-volume
      mountPath: /dev/shm
  - name: logging-agent
    image: <image2-name>
    volumeMounts:
    - name: logs
      mountPath: /opt/logs
  volumes:
  - name: logs
    source: local
  - name: models
    source: "@model_stage"
  - name: "my-mem-volume"
    source: memory
    size: 2G
Note that when you specify memory as the volume source, you must also specify the volumes.size field to indicate the memory size. For information about the memory size units you can specify, see About units.

About file permissions on mounted volumes
A container that mounts a Snowflake stage or a block storage volume typically runs as a root user. However, sometimes your container might run as a non-root user. For example:

If your application uses a third-party library, the library uses a non-root user to run application code inside the container.

For other reasons, such as security, you might run your application as a non-root user inside the container.

To avoid potential errors related to file user permissions, it’s important to set the UID (User ID) and GID (Group ID) of the container as part of the specification. This is particularly relevant for containers that use a specific user and group for launching or running the application within the container. By setting the appropriate UID and GID, you can use a container running as a non-root user. For example:

spec:
  ...

  volumes:
  - name: stagemount
    source: "@test"
    uid: <UID-value>
    gid: <GID-value>
Snowflake uses this information to mount the stage with appropriate permissions.

To obtain the UID and GID of the container, do the following:

Run the container locally using docker run.

Look up the container ID using the docker container list command. Partial sample output:

CONTAINER ID   IMAGE                       COMMAND
—----------------------------------------------------------
a6a1f1fe204d  tutorial-image         "/usr/local/bin/entr…"
Run the docker id command inside the container to get the UID and GID:

docker exec -it <container-id> id
Sample output:

uid=0(root) gid=0(root) groups=0(root)
spec.logExporters field (optional)
Snowflake collects your applications output to standard output or standard error. For more information, see Accessing local container logs. Use spec.logExporters to configure which of these outputs Snowflake exports to your event table.

logExporters:
  eventTableConfig:
    logLevel: < INFO | ERROR | NONE >
The supported logLevel values are:

INFO (default): Export all the user logs.

ERROR: Export only the error logs. Snowflake exports only the logs from stderr stream.

NONE: Do not export logs to the event table.

spec.platformMonitor field (optional)
Individual services publish metrics. These Snowflake-provided metrics are also referred to as the platform metrics. You add the spec.platformMonitor field in the specification to direct Snowflake to send metrics from the service to the event table configured for your account. The target use case for this is to observe resource utilization of a specific service.

platformMonitor:
  metricConfig:
    groups:
    - <group_1>
    - <group_2>
    ...
group_N refers to a predefined metrics groups that you are interested in. While the service is running, Snowflake logs metrics from specified groups to the event table. You can then query the metrics from the event table. For more information, see Monitoring Services.

About units
A service specification takes numeric values in several places. A variety of units are supported to express these values. For large and small values, you can use binary and decimal units as shown. In the following list, “#” represents an integer value.

Binary units:

numberKi means number*1024. For example, 4Ki is equivalent to 4096.

numberMi means number*1024*1024.

numberGi means number*1024*1024*1024.

Decimal units:

numberk means number*1000. For example, 4k is equivalent to 4000.

numberM means number*1000*1000.

numberG mean number*1000*1000*1000.

Fractional units:

numberm means number*0.001. For example, cpu: 500m is equivalent to cpu: 0.5.

capabilities field (optional)
In the capabilities top-level field in the specification, use the securityContext.executeAsCaller field to indicate the application intends to use caller’s rights.

capabilities:
  securityContext:
    executeAsCaller: <true / false>    # optional, indicates whether application intends to use caller’s rights
By default, executeAsCaller is false.

serviceRoles field (optional)
Use the serviceRoles top-level field in the specification to define one or more service roles. For each service role, provide a name and a list of one or more endpoints (defined in the spec.endpoints) you want the service role to grant USAGE privilege on.

serviceRoles:                   # Optional list of service roles
- name: <name>
  endpoints:
  - <endpoint-name>
  - <endpoint-name>
  - ...
- ...
Note the following:

Both the name and endpoints are required.

The service role name must adhere to the following format:

Must contain alphanumeric or _ characters.

Must start with an alphabetic character.

Must end with an alphanumeric character.
