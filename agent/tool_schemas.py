TOOLS = [
    {
        "name": "list_files",
        "description": "List files and directories under the given path.",
        "parameter_definitions": {
            "directory": {
                "description": "The directory path to list, relative to the repository root. Example: 'src'",
                "type": "str",
                "required": True
            }
        }
    },
    {
        "name": "read_file",
        "description": "Read a file's contents.",
        "parameter_definitions": {
            "path": {
                "description": "The path to the file to read, relative to the repository root. Example: 'src/humanize/number.py'",
                "type": "str",
                "required": True
            }
        }
    },
    {
        "name": "search_code",
        "description": "Search across the repository for a string or pattern.",
        "parameter_definitions": {
            "query": {
                "description": "The search query or pattern to find in the code.",
                "type": "str",
                "required": True
            }
        }
    },
    {
        "name": "write_file",
        "description": "Overwrite a file's full contents.",
        "parameter_definitions": {
            "path": {
                "description": "The path to the file to write, relative to the repository root.",
                "type": "str",
                "required": True
            },
            "content": {
                "description": "The new content to write into the file. This completely overwrites the file.",
                "type": "str",
                "required": True
            }
        }
    },
    {
        "name": "run_tests",
        "description": "Run the pytest suite against the given path.",
        "parameter_definitions": {
            "test_path": {
                "description": "The path to run tests on. Default is 'tests/'.",
                "type": "str",
                "required": False
            }
        }
    }
]
