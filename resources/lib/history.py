import os
from datetime import datetime
import sqlite3

import xbmc
import xbmcaddon

import constants, utils


addon = xbmcaddon.Addon(constants.ADDON_ID)

ADDON_DATA = xbmc.translatePath(addon.getAddonInfo('profile'))

HISTORY_FILE = os.path.join(ADDON_DATA, 'builds.db')


def maybe_create_database():
    with sqlite3.connect(HISTORY_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS builds
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL,
                         version TEXT NOT NULL, marked INTEGER default 0, comments TEXT,
                         UNIQUE(source, version))''')
        
        conn.execute('''CREATE UNIQUE INDEX IF NOT EXISTS source_version
                        ON builds (source, version)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS installs
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         build_id INTEGER REFERENCES builds(id),
                         timestamp TIMESTAMP NOT NULL)''')


@utils.logging("Added install {}|{} to database",
               "Failed to add install {}|{} to database")
def add_install(source, build):
    maybe_create_database()
    with sqlite3.connect(HISTORY_FILE) as conn:
        conn.execute('''INSERT OR IGNORE INTO builds (source, version)
                        VALUES (?, ?)''', (source, build.version))

        build_id = conn.execute('''SELECT last_insert_rowid()
                                   FROM builds''').fetchone()[0]
        if build_id == 0:
            build_id = get_build_id(source, build.version)

        conn.execute('''INSERT INTO installs (build_id, timestamp)
                        VALUES (?, ?)''', (build_id, datetime.now()))


def get_build_id(source, version):
    with sqlite3.connect(HISTORY_FILE) as conn:
        return conn.execute('''SELECT id FROM builds WHERE source = ? AND version = ?''',
                            (source, version)).fetchone()[0]


def get_install_history(source):
    with sqlite3.connect(HISTORY_FILE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        return conn.execute('''SELECT version, timestamp
                               FROM installs
                               JOIN builds ON builds.id = build_id
                               WHERE source = ?''', (source,)).fetchall()


def is_previously_installed(source, build):
    with sqlite3.connect(HISTORY_FILE) as conn:
        return bool(conn.execute('''SELECT COUNT(*) FROM installs WHERE
                                    source = ? AND version = ?''',
                                 (source, build.version)).fetchone()[0])