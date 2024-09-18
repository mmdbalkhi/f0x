# f0x

**f0x** is a minimal application designed to simplify file uploads and retrievals. It allows users to upload files  and retrieve them via a unique URL.

## Features

* **File Upload**: Upload files easily using a POST request.
* **File Retrieval**: Access uploaded files through a unique URL.
* **Minimalistic Design**: Focuses on simplicity and ease of use.

## Usage

### Uploading a File

To upload a file, send a POST request to the `/` endpoint with the file included in the request body.

Example using `curl` :

```sh
curl  -F 'file=@/path/to/your/file' 127.0.0.1:5000
```

### Retrieving a File

After uploading, you will receive a unique URL to access the file. Simply navigate to this URL in your browser or use it in your application to download the file.

## How to run

* Clone the repository:

```sh
git clone https://github.com/mmdbalkhi/f0x.git && cd f0x
```

* Install the required packages with pdm:

```sh
pdm install
```

* Run the application:

```sh
pdm run flask --app src/f0x/main.py run
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
