# pypi-offgrid.py

import os
import sys
import time
import toml
import click
import psutil
import platform
import requests

from pprint import pprint
from dotenv import load_dotenv

from flask import (
    Flask,
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    send_file,
    send_from_directory,
    stream_with_context,
    request,
    redirect,
    url_for,
)


sys.path.insert(0, 'D:\\work\\pypi_offgrid_private')
from app.config_file import ConfigFile
from app.application_conf import ApplicationConf
from app.cached_files import CachedFiles
from app.logger import get_logger
from app.db_sqlite import DBSQLite
from app.remote_simple_index import RemoteSimpleIndex


main = Blueprint('main', __name__)
app = Flask(__name__)


# will be set in run()
app_conf = None
logger = None
cached_files = None
db = None
remote_index = None
FLASK_LISTEN_IP = None
FLASK_LISTEN_PORT = None
PROXY_SERVER_BASE_URL = None
REMOTE_INDEX_SIMPLE = None
REMOTE_INDEX_JSON = None
CONNECTION_TIMEOUT = None
DOWNLOAD_TIMEOUT = None
MAX_RETRIES = None
LOG_FILE_PATH = None
DB_FILE_PATH = None
CACHE_DIR = None
WORKDIR = None



######## ########  ########   #######  ########       ##     ##    ###    ##    ## ########  ##       #### ##    ##  ######
##       ##     ## ##     ## ##     ## ##     ##      ##     ##   ## ##   ###   ## ##     ## ##        ##  ###   ## ##    ##
##       ##     ## ##     ## ##     ## ##     ##      ##     ##  ##   ##  ####  ## ##     ## ##        ##  ####  ## ##
######   ########  ########  ##     ## ########       ######### ##     ## ## ## ## ##     ## ##        ##  ## ## ## ##   ####
##       ##   ##   ##   ##   ##     ## ##   ##        ##     ## ######### ##  #### ##     ## ##        ##  ##  #### ##    ##
##       ##    ##  ##    ##  ##     ## ##    ##       ##     ## ##     ## ##   ### ##     ## ##        ##  ##   ### ##    ##
######## ##     ## ##     ##  #######  ##     ##      ##     ## ##     ## ##    ## ########  ######## #### ##    ##  ######


# Error handlers
@main.errorhandler(503)
def service_unavailable(error):
    """Service unavailable error handler."""
    logger.error("Service Unavailable: 503", exc_info=error)
    return "Service Unavailable", 503


@main.errorhandler(403)
def forbidden(error):
    """Forbidden error handler."""
    logger.error("Forbidden: 403", exc_info=error)
    return "Forbidden", 403


@main.errorhandler(404)
def not_found(error):
    """Not found error handler."""
    logger.error("Not Found: 404", exc_info=error)
    return "Not Found", 404


@main.errorhandler(408)
def request_timeout(error):
    """Request timeout error handler."""
    logger.error("Request Timeout: 408", exc_info=error)
    return "Request Timeout", 408


##       ######   #######  ##     ## ##     ##  #######  ##    ##      ########   #######  ##     ## ######## ########  ######
##      ##    ## ##     ## ###   ### ###   ### ##     ## ###   ##      ##     ## ##     ## ##     ##    ##    ##       ##    ##
##      ##       ##     ## #### #### #### #### ##     ## ####  ##      ##     ## ##     ## ##     ##    ##    ##       ##
##      ##       ##     ## ## ### ## ## ### ## ##     ## ## ## ##      ########  ##     ## ##     ##    ##    ######    ######
##      ##       ##     ## ##     ## ##     ## ##     ## ##  ####      ##   ##   ##     ## ##     ##    ##    ##             ##
##      ##    ## ##     ## ##     ## ##     ## ##     ## ##   ###      ##    ##  ##     ## ##     ##    ##    ##       ##    ##
##       ######   #######  ##     ## ##     ##  #######  ##    ##      ##     ##  #######   #######     ##    ########  ######


@main.route("/", strict_slashes=False)
def index_route():
    """Main index page."""
    logger.info("Received request for index page")
    return render_template(
        "index.html",
        proxy_server_base_url=PROXY_SERVER_BASE_URL,
    )


@main.route("/settings", strict_slashes=False)
def settings_route():

    # Get server IP and hostname
    server_ip = request.remote_addr
    server_hostname = platform.node()

    # Get operating system name and version
    os_name = platform.system()
    os_version = platform.release()

    # Get uptime and free space on the disk of cache directory
    uptime = time.time() - psutil.boot_time()
    cache_dir_path = CACHE_DIR
    cache_disk_free = psutil.disk_usage(cache_dir_path).free

    # db_human_file_size = cached_files.human_readable_size(os.path.getsize(DB_FILE_PATH))
    # log_human_file_size = cached_files.human_readable_size(os.path.getsize(LOG_FILE_PATH))

    server_info = {
#        "offline_mode": OFFLINE_MODE,
        "Listen IP": FLASK_LISTEN_IP,
        "Listen port": FLASK_LISTEN_PORT,
        "Proxy server base URL": PROXY_SERVER_BASE_URL,
        "Cache directory": f"{CACHE_DIR} (free space: {cached_files.human_readable_size(cache_disk_free)})",
        # "SQLite DB file path": f"{DB_FILE_PATH} (file size: {db_human_file_size})",
        # "Log file path": f"{LOG_FILE_PATH} (file size: {log_human_file_size})",
        "Remote index simple URL": REMOTE_INDEX_SIMPLE,
        "Remote index JSON URL": REMOTE_INDEX_JSON,
        "Connection timeout": CONNECTION_TIMEOUT,
        "Download timeout": DOWNLOAD_TIMEOUT,
        "Remote access retries": MAX_RETRIES,

        "Server OS": f"{os_name} {os_version}",
        "Server uptime": cached_files.human_readable_time(uptime),

    }

    return render_template(
        "settings.html",
        server_info=server_info,
    )


@main.route("/favicon.ico")
def favicon_route():
    """Favicon route."""
    logger.debug("Favicon requested")
    favicon_path = os.path.join(main.root_path, "static", "favicon.ico")
    return send_from_directory(
        os.path.dirname(favicon_path),
        os.path.basename(favicon_path),
        mimetype="image/vnd.microsoft.icon",
    )


##       ######  #### ##     ## ########  ##       ########
##      ##    ##  ##  ###   ### ##     ## ##       ##
##      ##        ##  #### #### ##     ## ##       ##
##       ######   ##  ## ### ## ########  ##       ######
##            ##  ##  ##     ## ##        ##       ##
##      ##    ##  ##  ##     ## ##        ##       ##
##       ######  #### ##     ## ##        ######## ########


@main.route("/simple/", strict_slashes=False)
def list_packages_route():
    """List all available packages as HTML."""
    logger.debug("Listing all packages")

    # TODO it was my mistake to call "project" a "package" and now i need to rename all the right way

    try:
        project_names = db.get_simple_all_names()
        # TODO rename "package_name" to "project_name"
        return render_template("simple_index.html", package_names=project_names)
    except Exception as e:
        logger.error("Failed to list packages", exc_info=e)
        return jsonify(error=str(e)), 500


@main.route("/simple/<project_name>/", strict_slashes=False)
def list_package_files_route(project_name):
    """List all files for a specific package as HTML."""
    logger.debug(f"Listing files for package {project_name}")

    try:
        # TODO implement OFFLINE_MODE
        project_links = remote_index.fetch_simple_links(project_name)
        db.save_simple_links(project_name, project_links)

        project_info = remote_index.fetch_pypi_json(project_name)
        db.save_package_json(project_name, project_info)

    except:
        logger.warning("Failed to get project info from remote index", exc_info=True)

    try:
        # load project data from DB
        simple_links = db.get_simple_links(project_name)
        if simple_links:
            # proxify links and return project page with links to packages
            proxified_links = {}

            for link in simple_links:
                for link_text, link_href in link.items():
                    proxified_link_href = cached_files.proxify_url(link_href)
                    proxified_links[link_text] = proxified_link_href

            return render_template(
                "simple_package.html",
                project_name=project_name,
                links=proxified_links,
            )

        else:
            # no records found or project contains no links -- return 404
            logger.warning(f"Project {project_name} not found")
            return f"Project {project_name} not found", 404

    except Exception as e:
        logger.error(f"Failed to list files for package {project_name}", exc_info=e)
        return jsonify(error=str(e)), 500


@main.route(
    "/download_file/<string:base64_host>/<path:file_path>",
    methods=["GET"],
    strict_slashes=False,
)
def download_file_route(base64_host, file_path):
    """
    Fast and efficient file download from remote server, with caching.

    Args:
        base64_host (str): Base64 encoded host URL.
        file_path (str): Path to the file to download.

    Returns:
        Response: Response object containing the downloaded file.
    """

    # Decode the host URL and convert it to project_name
    remote_url = cached_files.deproxify_url(base64_host, file_path)
    logger.info(f"request to download file {remote_url} ")
    logger.debug(f"download_file_route: {base64_host} {file_path}")

    # Convert URL file path to the local absolute path in the cache directory
    cached_file_path = cached_files.convert_url_to_file_path(remote_url)

    if os.path.exists(cached_file_path):
        # File is already in cache: send it to user
        logger.debug(f"download_file_route: FILE ALREADY CACHED {cached_file_path}")
        return send_from_directory(
            os.path.dirname(cached_file_path), os.path.basename(cached_file_path)
        )

    # elif OFFLINE_MODE:
    #     # File is not in cache, but offline mode is enabled: return http error "503 Service Unavailable"
    #     return "Service Unavailable (Offline Mode Enabled)", 503

    else:
        # File is not in cache: start downloading, at the same time sending it to user
        # Downloading goes into temporary file, which is renamed into permanent one if (and only if) download is successful
        logger.debug(f"download_file_route: FILE DOES NOT CACHED {remote_url}")

        # Prepare the temporary file path
        # temp_file_path = helpers.append_temporary_file_suffix(cached_file_path)
        temp_file_path = cached_files.get_temporary_file_name(cached_file_path)

        # Prepare target directories for the downloading files
        cached_files.create_directories(
            [
                cached_files.extract_parent_directory(cached_file_path),
                cached_files.extract_parent_directory(temp_file_path),
            ]
        )
        # helpers.prepare_directory_for_file(cached_file_path)
        # helpers.prepare_directory_for_file(temp_file_path)

        # Create the download_stream to remote_url with timeouts CONNECTION_TIMEOUT and DOWNLOAD_TIMEOUT
        download_stream = requests.get(
            remote_url,
            stream=True,
            timeout=(CONNECTION_TIMEOUT, DOWNLOAD_TIMEOUT),
        )

        def stream_and_save():
            with open(temp_file_path, "wb") as f:
                for chunk in download_stream.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        yield chunk

            # When (and if) file is downloaded, rename it from temporary name to permanent one
            logger.debug(
                f"download_file_route: rename {temp_file_path} to {cached_file_path}"
            )
            os.rename(temp_file_path, cached_file_path)

        # Return the response object containing the downloaded file
        return Response(
            stream_with_context(stream_and_save()),
            content_type=download_stream.headers["content-type"],
            direct_passthrough=True,
        )


##       ######     ###     ######  ##     ## ########            ######  ########    ###    ######## ##     ##  ######
##      ##    ##   ## ##   ##    ## ##     ## ##                 ##    ##    ##      ## ##      ##    ##     ## ##    ##
##      ##        ##   ##  ##       ##     ## ##                 ##          ##     ##   ##     ##    ##     ## ##
##      ##       ##     ## ##       ######### ######              ######     ##    ##     ##    ##    ##     ##  ######
##      ##       ######### ##       ##     ## ##                       ##    ##    #########    ##    ##     ##       ##
##      ##    ## ##     ## ##    ## ##     ## ##                 ##    ##    ##    ##     ##    ##    ##     ## ##    ##
##       ######  ##     ##  ######  ##     ## ######## #########  ######     ##    ##     ##    ##     #######   ######


@main.route("/cache_status/", strict_slashes=False)
def cache_status_route():
    return render_template("cache_status_index.html")


# TODO напиши эндпоинт /cache_status/project_files/<project_name>, который получает из БД список simple_links для проекта, обрабатывает и передает в HTML список словарей: project_name, original_url, proxified_url, cached_file_path, file_size (если файла нет,то file_size=None). возвращаемый список должен быть отсортирован по (file_size, file_name): файлы с размером None должны быть в конце списка
@main.route("/cache_status/project_files/<project_name>/", strict_slashes=False)
def cache_status_project_files_route(project_name):
    simple_links = db.get_simple_links(project_name)
    # pprint(simple_links)
    if simple_links is None:
        return "Project not found", 404

    else:
        project_files_info = []
        for link in simple_links:
            for link_text, link_href in link.items():
                project_files_info.append(
                    cached_files.get_cached_file_info(link_href, link_text)
                )

        # Sort by file_size (None values will be sorted to the end), then by file_name
        project_files_info.sort(key=lambda x: (not x["file_exists"], x["file_name"]))

        return render_template(
            "cache_status_files.html",
            project_name=project_name,
            project_files_info=project_files_info,
        )


@main.route("/cache_status/<project_name>/", strict_slashes=False)
def cache_status_files_route(project_name):
    """Returns caching status of project files in HTML format"""
    # Fetch project data from the database and render cache_status_project.html template with it
    project_info = db.get_project_info(project_name)
    if project_info is None:
        return "Project not found in cache", 404

    return render_template(
        "cache_status_info.html",
        project_name=project_name,
        project_info=project_info,
        proxy_server_base_url=PROXY_SERVER_BASE_URL,
    )


##         ###          ##    ###    ##      ##      ######## ##    ## ########  ########   #######  #### ##    ## ########  ######
##        ## ##         ##   ## ##    ##    ##       ##       ###   ## ##     ## ##     ## ##     ##  ##  ###   ##    ##    ##    ##
##       ##   ##        ##  ##   ##    ##  ##        ##       ####  ## ##     ## ##     ## ##     ##  ##  ####  ##    ##    ##
##      ##     ##       ## ##     ##    ####         ######   ## ## ## ##     ## ########  ##     ##  ##  ## ## ##    ##     ######
##      ######### ##    ## #########   ##  ##        ##       ##  #### ##     ## ##        ##     ##  ##  ##  ####    ##          ##
##      ##     ## ##    ## ##     ##  ##    ##       ##       ##   ### ##     ## ##        ##     ##  ##  ##   ###    ##    ##    ##
##      ##     ##  ######  ##     ## ##      ##      ######## ##    ## ########  ##         #######  #### ##    ##    ##     ######


# @main.route("/webapi/get_offline_mode", strict_slashes=False)
# def get_offline_mode():

#     ret_value = "on" if OFFLINE_MODE else "off"

#     logger.debug(f"get_offline_mode requested, returning {ret_value}")
#     return jsonify(ret_value)


# @main.route("/webapi/set_offline_mode/<string:value>", strict_slashes=False)
# def set_offline_mode(value):
#     global OFFLINE_MODE
#     OFFLINE_MODE = value.lower() in ["true", "on"]
#     db.set_prefs_value("offline_mode", OFFLINE_MODE)
#     logger.debug(f"set_offline_mode requested, setting to {OFFLINE_MODE}")
#     return jsonify(OFFLINE_MODE)


@main.route("/webapi/list_projects/", strict_slashes=False)
def list_all_projects():
    return list_filtered_paginated_projects(
        items_per_page=None, page_number=None, prj_mask=None
    )


@main.route(
    "/webapi/list_projects/<int(signed=True):items_per_page>/<int(signed=True):page_number>",
    strict_slashes=False,
)
def list_paginated_projects(items_per_page=20, page_number=1):
    return list_filtered_paginated_projects(items_per_page, page_number, None)


@main.route(
    "/webapi/list_projects/<int(signed=True):items_per_page>/<int(signed=True):page_number>/<path:prj_mask>",
    strict_slashes=False,
)
def list_filtered_paginated_projects(items_per_page, page_number, prj_mask=None):
    if prj_mask is None:
        prj_mask = "*"
    logger.debug(
        f"list_projects requested, prj_mask: {prj_mask}, items_per_page: {items_per_page}, page_number: {page_number}"
    )
    project_names = db.get_simple_advanced(prj_mask, items_per_page, page_number)
    project_descriptions = {
        project_name: db.get_project_summary(project_name)
        for project_name in project_names
    }
    ret_json = jsonify(project_descriptions)
    return ret_json



    
##       ######  ##       ####  ######  ##     ## 
##      ##    ## ##        ##  ##    ## ##    ##  
##      ##       ##        ##  ##       ##   ##   
##      ##       ##        ##  ##       #####     
##      ##       ##        ##  ##       ##   ##   
##      ##    ## ##        ##  ##    ## ##    ##  
##       ######  ######## ####  ######  ##     ## 
    
    
@click.group()
def cli():
    pass

@cli.command()
@click.argument('workdir')
def run(workdir):
    global app_conf    
    global WORKDIR
    global FLASK_LISTEN_IP
    global FLASK_LISTEN_PORT
    global PROXY_SERVER_BASE_URL
    global REMOTE_INDEX_SIMPLE
    global REMOTE_INDEX_JSON
    global CONNECTION_TIMEOUT
    global DOWNLOAD_TIMEOUT
    global MAX_RETRIES
    global LOG_FILE_PATH
    global DB_FILE_PATH
    global CACHE_DIR
    global app_conf
    global app
    global main
    global logger
    global cached_files
    global db
    global remote_index
    
            
    app_conf = ApplicationConf(workdir, 'pypi-offgrid.toml')
    
    WORKDIR = workdir
    FLASK_LISTEN_IP = app_conf.FLASK_LISTEN_IP
    FLASK_LISTEN_PORT = app_conf.FLASK_LISTEN_PORT
    PROXY_SERVER_BASE_URL = app_conf.PROXY_SERVER_BASE_URL
    REMOTE_INDEX_SIMPLE = app_conf.REMOTE_INDEX_SIMPLE
    REMOTE_INDEX_JSON = app_conf.REMOTE_INDEX_JSON
    CONNECTION_TIMEOUT = app_conf.CONNECTION_TIMEOUT
    DOWNLOAD_TIMEOUT = app_conf.DOWNLOAD_TIMEOUT
    MAX_RETRIES = app_conf.MAX_RETRIES
    # LOG_FILE_PATH = app_conf.LOG_FILE_PATH
    DB_FILE_PATH = app_conf.DB_FILE_PATH
    CACHE_DIR = app_conf.CACHE_DIR

    app.register_blueprint(main)
    app.logger.propagate = True
    app.debug = True    
    
    logger = get_logger(WORKDIR, "messages.log")
    logger.debug("views.py loaded")
    
    cached_files = CachedFiles(logger, CACHE_DIR, PROXY_SERVER_BASE_URL, "download_file")
    db = DBSQLite(DB_FILE_PATH)
    remote_index = RemoteSimpleIndex(
        logger,
        simple_url=REMOTE_INDEX_SIMPLE,
        json_url=REMOTE_INDEX_JSON,
        connect_timeout=CONNECTION_TIMEOUT,
        download_timeout=DOWNLOAD_TIMEOUT,
        max_retries=MAX_RETRIES,
    )

    
    app.config['WORKDIR'] = workdir
    app.run(host=FLASK_LISTEN_IP, port=FLASK_LISTEN_PORT)

@cli.command()
@click.argument('workdir')
def init(workdir):
    
    click.echo(f'Инициализация рабочего каталога: {workdir}')

@cli.command()
def version():
    click.echo('Версия приложения: 1.0.0')

if __name__ == '__main__':
    cli()
