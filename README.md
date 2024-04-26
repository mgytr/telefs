# teleFS

A simple FUSE file system that uses Telegram as a backend.

## Installation

```bash
pip install -r requirements.txt
sudo apt install fuse libfuse-dev # or equivalent
# Edit .env file and add your Telegram Bot Token Chat ID
```

## Usage

```bash
python3 main.py --mount <mountpoint> [--background]
```

## Features

- [x] Read files
- [x] Write files
- [x] Append to files
- [x] Create directories
- [x] Delete files & directories
- [x] List files & directories
- [x] Move files & directories
- [ ] File locking
- [ ] Metadata

## Never Features

- Ownership
- File versioning
- Permissions

## License

MIT

```
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
