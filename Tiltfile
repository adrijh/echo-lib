LIB_DIR = config.main_dir

def echo_lib_sync(local_path=None, path_in_container='/app/echo-lib'):
    src = local_path or config.main_dir
    return [
        sync(src, path_in_container),
        run('uv pip install --system -e ' + path_in_container, trigger=[src]),
    ]

def echo_lib_path():
    return os.path.dirname(config.main_dir)
